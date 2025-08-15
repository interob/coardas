"""
Accessor and Assimilator classes for products in the Copernicus Global Land Service (CGLS) programme. The Accessor
class plugs in to the cataloging system based on manifest end point as current hosted by VITO.

Author: Rob Marjot, March 2023
"""

import logging
import re
import shutil
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Generator

import requests
from tqdm import tqdm

from coardas.cgls.product import CGLSProduct
from coardas.cgls.translator import CGLSTranslator
from coardas.objects.timeslicing import Dekad

log = logging.getLogger(__name__)


class CGLSProductAccessor:
    """
    Facilitates access to products: download files that are not in the mirror.
    """

    BUFFER_SIZE: int = 4096

    def __init__(
        self,
        username: str,
        password: str,
        product: CGLSProduct,
        mirror: Path | None = None,
        mirror_is_readonly: bool = False,
        scratch_dir: Path | None = None,
    ) -> None:
        self.__username = username
        self.__password = password
        self.__product = product
        self.__mirror = mirror
        self.__mirror_is_readonly = mirror_is_readonly if mirror is not None else True
        # immediately load manifest and keep:
        self.__manifest = requests.get(product.manifest_url).text.splitlines()
        self.__scratch_dir = scratch_dir

    @property
    def product(self):
        return self.__product

    def __get_manifest_index(self, patn_manifest: str) -> tuple[int, re.Match | None]:
        patn: re.Pattern = re.compile(f".+{patn_manifest}$")
        for i, datafile in enumerate(self.__manifest):
            if m := patn.match(datafile):
                return (i, m)
        return (-1, None)

    def is_advertised(self, timestep: Dekad) -> bool:
        path = timestep.resolve(self.__product.patn_manifest)
        return self.__get_manifest_index(path)[0] >= 0

    @contextmanager
    def download(
        self, timestep: Dekad, target_location: Path = None, return_mirror_location: bool = True
    ) -> Generator[Path | None, None, None]:
        """
        Robust downloading of the data file or retrieval from mirror. When actual download is needed and  the accesor
        is configured to have a non read-only mirror, the download is saved in mirror -- in which case the download may
        (option: return_mirror_location) return the direct path to the  mirror location for the downloaded file without
        copying to the target location (not passing a target location implicies returning of mirror location!).
        """

        i, m = self.__get_manifest_index(timestep.resolve(self.__product.patn_manifest))
        if i < 0:
            yield None
            return

        datafile = timestep.resolve(
            self.__product.patn_datafile, None if m is None else m.groupdict()
        )

        mirrorfile: Path = None
        targetfile: Path = None
        if self.__mirror is not None:
            mirrorfile = self.__mirror.joinpath(datafile)
        if target_location is not None:
            targetfile = target_location.joinpath(datafile)
        elif mirrorfile is not None:
            targetfile = mirrorfile
        else:
            targetfile = self.__scratch_dir.joinpath(datafile)

        if targetfile.exists():
            yield targetfile
            return

        if mirrorfile is not None and mirrorfile.exists():
            if not return_mirror_location and mirrorfile != targetfile:
                shutil.copy(mirrorfile, targetfile)
                try:
                    yield targetfile
                finally:
                    if target_location is None:
                        targetfile.unlink()
                    return
            yield mirrorfile
            return
        elif mirrorfile is None or self.__mirror_is_readonly:
            if mirrorfile == targetfile:
                raise RuntimeError(f"Attempt to write to read-only mirror! ({mirrorfile})")
            downloadfile = targetfile.with_suffix(".coardasdl")
        else:
            downloadfile = mirrorfile.with_suffix(".coardasdl")

        session = requests.Session()
        session.auth = (self.__username, self.__password)
        r = session.get(self.__manifest[i], stream=True)

        total_size = int(r.headers.get("content-length", 0))
        pbar = tqdm(total=total_size, unit="iB", unit_scale=True)

        downloadfile.parent.mkdir(parents=True, exist_ok=True)
        with downloadfile.open("wb") as f:
            for data in r.iter_content(CGLSProductAccessor.BUFFER_SIZE):
                pbar.update(len(data))
                f.write(data)
        pbar.close()

        if mirrorfile is not None and not self.__mirror_is_readonly:
            shutil.move(downloadfile, mirrorfile)
            if not return_mirror_location and mirrorfile != targetfile:
                shutil.copy(mirrorfile, targetfile)
                try:
                    yield targetfile
                finally:
                    if target_location is None:
                        targetfile.unlink()
                    return
            yield mirrorfile
            return
        else:
            shutil.move(downloadfile, targetfile)
            try:
                yield targetfile
            finally:
                if target_location is None:
                    targetfile.unlink()
                return


class CGLSProductAssimilator:
    """
    Assimilates multiple CGLS products in a single archive. Operation:
      - Overlap is resolved through first come, first serve (in order of being added to the assimilator)
      - Spatial resampling is handled as needed, using pre-defined resampling routine on product level

    Currently, CGLSProductAssimilator can only handle products with a dekadal temporal resolution.

    Output format is GeoTIFF.
    """

    def __init__(
        self,
        target_resolution: str,
        target_aoi: tuple[float, float, float, float],
        output_dir: Path,
        naming_pattern: str,
        begin_date: datetime,
        end_date: datetime,
        username: str,
        password: str,
        scratch: Path = None,
    ) -> None:
        self.__products: list[CGLSProductAccessor] = []
        self.__resamplers: list[CGLSTranslator] = []
        self.__target_resolution = target_resolution
        self.__target_aoi = target_aoi
        self.__output_dir = output_dir
        self.__naming_pattern = naming_pattern
        self.__begin_date = begin_date
        self.__end_date = end_date
        self.__username = username
        self.__password = password
        self.__aligned_aoi = None
        self.__scratch = scratch

    @property
    def output_dir(self):
        return self.__output_dir

    @property
    def target_resolution(self):
        return self.__target_resolution

    @property
    def target_aoi(self):
        return self.__target_aoi

    @property
    def aligned_aoi(self):
        return self.__aligned_aoi

    def add(
        self, product: CGLSProduct, mirror: Path | None = None, mirror_is_readonly: bool = False
    ):
        self.__products.append(
            CGLSProductAccessor(
                self.__username,
                self.__password,
                product,
                mirror,
                mirror_is_readonly,
                self.__scratch,
            )
        )

    def prepare(self) -> bool:
        # runs through begin - end to find first hit of every product
        # prepare aligned aoi
        product_first_hit: dict[int, Dekad] = {}
        cursor: Dekad = Dekad(self.__begin_date)
        while not cursor.ends_after(Dekad(self.__end_date)):
            i = 0
            while i < len(self.__products):
                if self.__products[i].is_advertised(cursor):
                    break
                i += 1
            if i == len(self.__products):
                log.error(f"No product found for {cursor}")
                return False
            if i not in product_first_hit:
                product_first_hit[i] = cursor
            if len(product_first_hit) == len(self.__products):
                break
            cursor += 1

        translators: list[CGLSTranslator] = []

        def find_aligned_aoi(start_at: int) -> tuple[float, float, float, float] | None:
            """
            Establishes an AOI that nicely aligns across translators; searches recursively as-needed
            for a box (worldly coordinates) that sufficiently aligns (at 8 decimals). Such an AOI does
            not need to align in pixel space (e.g. 336/112 ratio is shape is not enforced).
            """

            if start_at < 0 or start_at > (len(translators) - 1):
                return None
            _tested_aoi = translators[start_at].get_aligned_aoi(self.target_aoi)
            for i, t in enumerate(translators):
                if i == start_at:
                    continue
                if not CGLSTranslator.aois_are_equal(t.get_aligned_aoi(_tested_aoi), _tested_aoi):
                    return find_aligned_aoi(start_at - 1, self.target_aoi)
            return _tested_aoi

        for i, dekad in product_first_hit.items():
            with self.__products[i].download(dekad, self.__scratch) as datafile:
                translators.append(
                    self.__products[i].product.get_translator(
                        datafile, self.__products[i].product.variable, self.target_resolution
                    )
                )
                self.__aligned_aoi = find_aligned_aoi(len(translators) - 1)
                if self.__aligned_aoi is None:
                    log.error("Unable to establish an aligned AOI across products")
                    return False

        return True

    def ingest(self):
        assert self.__aligned_aoi is not None

        def access_and_translate(dekad: Dekad) -> Path | None:
            for product in self.__products:
                if product.is_advertised(dekad):
                    with product.download(dekad) as datafile:
                        t = product.product.get_translator(
                            datafile, product.product.variable, self.target_resolution
                        )
                        assert CGLSTranslator.aois_are_equal(
                            t.get_aligned_aoi(self.aligned_aoi), self.aligned_aoi
                        )
                        return t.translate(
                            datafile,
                            product.product.variable,
                            self.aligned_aoi,
                            self.output_dir.joinpath(dekad.resolve(self.__naming_pattern)),
                        )

        cursor: Dekad = Dekad(self.__begin_date)
        while not cursor.ends_after(Dekad(self.__end_date)):
            if not self.output_dir.joinpath(cursor.resolve(self.__naming_pattern)).exists():
                if access_and_translate(cursor) is None:
                    return

            cursor += 1
