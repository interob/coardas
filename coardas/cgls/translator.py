"""
Translator classes implementing robust subsetting and resampling, while aligning dataset archives into
a single extented time series. This class also maps the nominal reolutions (labels like: 300m, 1km) to
actual pixels per degree.

Author: Rob Marjot, March 2023
"""

import logging
from pathlib import Path

import numpy as np
import rasterio
import rioxarray as rio
import xarray as xr
from rasterio.io import BufferedDatasetWriter

log = logging.getLogger(__name__)


class CGLSTranslator:
    """
    Basic translator that can do subsetting on an image without any resampling. An AOI is
    aligned to full pixels.
    """

    __resolution_pixel_per_degree: dict[str, int] = {"1km": 112, "300m": 336}

    @staticmethod
    def pixels_per_degree(resolution: str) -> int:
        try:
            return CGLSTranslator.__resolution_pixel_per_degree[resolution]
        except KeyError:
            return 0

    @staticmethod
    def aois_are_equal(the_one, the_other):
        return (
            round(the_one[0]) == round(the_other[0], 8)
            and round(the_one[1]) == round(the_other[1], 8)
            and round(the_one[2]) == round(the_other[2], 8)
            and round(the_one[3]) == round(the_other[3], 8)
        )

    def __init__(
        self,
        gt: tuple[float, float, float, float, float, float],
        shape: tuple[int, int],
        lats: list[float],
        lons: list[float],
        native_resolution: int,
        scale_factor: float,
        add_offset: float,
        fill_value: int,
    ) -> None:
        super().__init__()
        self.__gt = gt
        self.__shape = shape
        self.__lats = lats
        self.__lons = lons
        self.__native_resolution = native_resolution
        self.__scale_factor = scale_factor
        self.__add_offset = add_offset
        self.__fill_value = fill_value

    @property
    def fill_value(self):
        return self.__fill_value

    @property
    def scale_factor(self):
        return self.__scale_factor

    @property
    def add_offset(self):
        return self.__add_offset

    @property
    def gt(self) -> tuple[float, float, float, float, float, float]:
        return self.__gt

    @property
    def shape(self) -> tuple[int, int]:
        return self.__shape

    @property
    def lats(self) -> tuple[float]:
        return self.__lats

    @property
    def lons(self) -> list[float]:
        return self.__lons

    @property
    def native_resolution(self) -> int:
        return self.__native_resolution

    def get_aligned_aoi(
        self, my_ext: tuple[float, float, float, float]
    ) -> tuple[float, float, float, float]:
        def find_nearest(array, value):
            array = np.asarray(array)
            idx = (np.abs(array - value)).argmin()
            return array[idx]

        assert my_ext[0] <= my_ext[2], (
            "min Longitude is bigger than correspond Max, pls change position or check values."
        )
        assert my_ext[1] >= my_ext[3], (
            "min Latitude is bigger than correspond Max, pls change position or check values."
        )
        assert self.lons[0] <= my_ext[0] <= self.lons[-1], (
            "min Longitudinal value out of original dataset Max ext."
        )
        assert self.lats[-1] <= my_ext[1] <= self.lats[0], (
            "Max Latitudinal value out of original dataset Max ext."
        )

        assert self.lons[0] <= my_ext[2] <= self.lons[-1], (
            "Max Longitudinal value out of original dataset Max ext."
        )
        assert self.lats[-1] <= my_ext[3] <= self.lats[0], (
            "min Latitudinal value out of original dataset Max ext."
        )

        return (
            find_nearest(self.lons, my_ext[0]),
            find_nearest(self.lats, my_ext[1]),
            find_nearest(self.lons, my_ext[2]),
            find_nearest(self.lats, my_ext[3]),
        )

    def translate(
        self,
        datafile: Path,
        variable: str,
        my_ext: tuple[float, float, float, float],
        output_path: Path,
    ) -> Path | None:
        """
        Translate the data: subset and store as TIFF
        """

        def sign(value) -> int:
            return 1 if value >= 0 else -1

        def find_nearest(array, value):
            array = np.asarray(array)
            return (np.abs(array - value)).argmin()

        window = (
            find_nearest(self.lons, my_ext[0]),
            find_nearest(self.lats, my_ext[1]),
            find_nearest(self.lons, my_ext[2]),
            find_nearest(self.lats, my_ext[3]),
        )

        __options = {**xr.get_options().mapping}
        try:
            try:
                xr.set_options(keep_attrs=True)
                rio.set_options(skip_missing_spatial_dims=False)
                with xr.open_dataset(datafile, mask_and_scale=False) as ds:
                    valid_range = ds[variable].attrs["valid_range"]
                    ds: xr.Dataset
                    grid = (
                        ds[variable]
                        .isel(lon=slice(window[0], window[2]), lat=slice(window[1], window[3]))
                        .to_numpy()
                    )[0, :, :]
                    grid = np.where(
                        (grid >= valid_range[0]) & (grid <= valid_range[1]),
                        grid,
                        ds[variable].attrs["_FillValue"],
                    )

                    output_path = output_path.with_suffix(".tif")
                    if output_path.exists():
                        output_path.unlink()
                    else:
                        output_path.parent.mkdir(parents=True, exist_ok=True)

                    log.info(f"Writing: {output_path}...")
                    with rasterio.open(
                        output_path,
                        "w",
                        width=window[2] - window[0],
                        height=window[3] - window[1],
                        count=1,
                        crs="EPSG:4326",
                        transform=rasterio.Affine.from_gdal(
                            round(my_ext[0] - (0.5 / self.native_resolution), 8),
                            round(sign(self.gt[1]) * (1 / self.native_resolution), 8),
                            0.0,
                            round(my_ext[1] + (0.5 / self.native_resolution), 8),
                            0.0,
                            round(sign(self.gt[5]) * (1 / self.native_resolution), 8),
                        ),
                        dtype=str(grid.dtype),
                        nodata=ds[variable].attrs["_FillValue"],
                        driver="COG",
                        blocksize=256,
                        compress="LZW",
                        level=9,
                        overviews="NONE",
                    ) as cog:
                        cog: BufferedDatasetWriter
                        cog.offsets = [ds[variable].attrs["add_offset"]]
                        cog.scales = [ds[variable].attrs["scale_factor"]]
                        cog.write(grid, 1)
                        return output_path

            except Exception as ex:
                str(ex)
                return None
        finally:
            try:
                __options.pop("enable_cftimeindex", None)
                xr.set_options(**__options)
            except Exception:
                pass

    @classmethod
    def from_netcf(cls, datafile: Path) -> "CGLSTranslator":
        with xr.open_dataset(datafile.as_posix(), mask_and_scale=False) as ds:
            return cls(list(ds.lat.values), list(ds.lon.values))


class CGLSResamplingTranslator(CGLSTranslator):
    def __init__(
        self,
        gt: tuple[float, float, float, float, float, float],
        shape: tuple[int, int],
        lats: list[float],
        lons: list[float],
        native_resolution: int,
        target_resolution: int,
        scale_factor: float,
        add_offset: float,
        fill_value: int,
    ) -> None:
        super().__init__(
            gt, shape, lats, lons, native_resolution, scale_factor, add_offset, fill_value
        )
        assert (native_resolution % target_resolution) == 0
        self.__target_resolution = target_resolution

    @property
    def target_resolution(self):
        return self.__target_resolution

    def get_aligned_aoi(
        self, my_ext: tuple[float, float, float, float]
    ) -> tuple[float, float, float, float]:
        def find_nearest(array, value):
            array = np.asarray(array)
            idx = (np.abs(array - value)).argmin()
            return array[idx]

        def sign(value) -> int:
            return 1 if value >= 0 else -1

        assert my_ext[0] <= my_ext[2], (
            "min Longitude is bigger than correspond Max, pls change position or check values."
        )
        assert my_ext[1] >= my_ext[3], (
            "min Latitude is bigger than correspond Max, pls change position or check values."
        )
        assert (
            self.lons[0] <= my_ext[0] <= self.lons[-1]  # ds.lon
        ), "min Longitudinal value out of original dataset Max ext."
        assert self.lats[-1] <= my_ext[1] <= self.lats[0], (
            "Max Latitudinal value out of original dataset Max ext."
        )

        assert self.lons[0] <= my_ext[2] <= self.lons[-1], (
            "Max Longitudinal value out of original dataset Max ext."
        )
        assert self.lats[-1] <= my_ext[3] <= self.lats[0], (
            "min Latitudinal value out of original dataset Max ext."
        )

        dy = round(self.shape[0] * sign(self.gt[5]) * (1 / self.native_resolution))
        dx = round(self.shape[1] * sign(self.gt[1]) * (1 / self.native_resolution))
        lat_target = np.round(np.arange(80.0, -60.0, -1.0 / 112), 8)
        lat_target = np.round(
            np.arange(self.gt[3], self.gt[3] + dy, sign(self.gt[5]) / self.target_resolution), 8
        )
        lat_target = np.arange(
            self.gt[3], self.gt[3] + dy, sign(self.gt[5]) / self.target_resolution
        )
        lon_target = np.round(np.arange(-180.0, 180.0, 1.0 / 112), 8)
        lon_target = np.round(
            np.arange(self.gt[0], self.gt[0] + dx, sign(self.gt[1]) / self.target_resolution), 8
        )
        lon_target = np.arange(
            self.gt[0], self.gt[0] + dx, sign(self.gt[1]) / self.target_resolution
        )
        return (
            # UL
            find_nearest(self.lons, find_nearest(lon_target, my_ext[0])),
            find_nearest(self.lats, find_nearest(lat_target, my_ext[1])),
            # LR
            find_nearest(self.lons, find_nearest(lon_target, my_ext[2])),
            find_nearest(self.lats, find_nearest(lat_target, my_ext[3])),
        )

    def translate(
        self,
        datafile: Path,
        variable: str,
        my_ext: tuple[float, float, float, float],
        output_path: Path,
    ) -> Path | None:
        def sign(value) -> int:
            return 1 if value >= 0 else -1

        log.info(f"Translating: {datafile}...")

        with xr.open_dataset(datafile, mask_and_scale=False) as ds:
            chunks = dict(zip(ds[variable].dims, ds[variable].encoding["chunksizes"]))
        with xr.open_dataset(datafile, mask_and_scale=False, chunks=chunks) as ds:
            aoi = self.get_aligned_aoi(my_ext)
            da: xr.DataArray = ds[variable].sel(
                lon=slice(aoi[0], aoi[2]), lat=slice(aoi[1], aoi[3])
            )

            __options = {**xr.get_options().mapping}
            try:
                xr.set_options(keep_attrs=True)
                rio.set_options(skip_missing_spatial_dims=False)
                try:
                    # Create the mask according to the fixed values
                    valid_range = ds[variable].attrs["valid_range"]
                    da_msk = da.where((da >= valid_range[0]) & (da <= valid_range[1]))

                    # Create the coarsen dataset
                    factor = self.native_resolution // self.target_resolution
                    coarsen = da_msk.coarsen(lat=factor, lon=factor, boundary="trim").mean()

                    # Force results to integer
                    coarsen_int: xr.DataArray = np.rint(coarsen)

                    # Mask the dataset according to the minumum required values
                    vo = xr.where((da >= valid_range[0]) & (da <= valid_range[1]), 1, 0)
                    vo_cnt = vo.coarsen(lat=factor, lon=factor, boundary="trim").sum()

                    # Mask the dataset according to the minumum required values
                    grid = (
                        coarsen_int.where(vo_cnt >= 5, ds[variable].attrs["_FillValue"])
                        .to_numpy()
                        .astype(np.dtype("B"))
                    )[0, :, :]
                    output_path = output_path.with_suffix(".tif")
                    if output_path.exists():
                        output_path.unlink()
                    else:
                        output_path.parent.mkdir(parents=True, exist_ok=True)

                    log.info(f"Writing: {output_path}...")
                    with rasterio.open(
                        output_path,
                        "w",
                        width=grid.shape[1],
                        height=grid.shape[0],
                        count=1,
                        crs="EPSG:4326",
                        transform=rasterio.Affine.from_gdal(
                            round(my_ext[0] - (0.5 / self.target_resolution), 8),
                            round(sign(self.gt[1]) * (1 / self.target_resolution), 8),
                            0.0,
                            round(my_ext[1] + (0.5 / self.target_resolution), 8),
                            0.0,
                            round(sign(self.gt[5]) * (1 / self.target_resolution), 8),
                        ),
                        dtype=str(grid.dtype),
                        nodata=ds[variable].attrs["_FillValue"],
                        driver="COG",
                        blocksize=256,
                        compress="LZW",
                        level=9,
                        overviews="NONE",
                    ) as cog:
                        cog: BufferedDatasetWriter
                        cog.offsets = [ds[variable].attrs["add_offset"]]
                        cog.scales = [ds[variable].attrs["scale_factor"]]
                        cog.write(grid, 1)
                        return output_path

                except Exception as ex:
                    template = "An exception of type {0} occurred. Arguments:\n{1!r}"
                    message = template.format(type(ex).__name__, ex.args)
                    log.error(message)
                    raise
            finally:
                try:
                    __options.pop("enable_cftimeindex", None)
                    xr.set_options(**__options)
                except BaseException:
                    pass
