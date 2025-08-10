"""
Ingest utility: concatenates available archives of compatible datasets into a single time series

Author: Rob Marjot, March 2023
"""

import logging
import sys
import tempfile
from datetime import datetime
from pathlib import Path

import click

from coardas.cgls.accessor import CGLSProductAssimilator
from coardas.cgls.product import (
    CGLS_NDVI1K_GLOBE_PROBAV_V301,
    CGLS_NDVI1K_GLOBE_VGT_V301,
    CGLS_NDVI300_GLOBE_OLCI_V201,
    CGLSProduct,
)

__products: dict[str, CGLSProduct] = {
    "CGLS_NDVI1K_GLOBE_VGT_V301": CGLS_NDVI1K_GLOBE_VGT_V301,
    "CGLS_NDVI1K_GLOBE_PROBAV_V301": CGLS_NDVI1K_GLOBE_PROBAV_V301,
    "CGLS_NDVI300_GLOBE_OLCI_V201": CGLS_NDVI300_GLOBE_OLCI_V201,
}


@click.command()
@click.argument(
    "products",
    nargs=-1,
    type=click.Choice(
        [
            "CGLS_NDVI300_GLOBE_OLCI_V201",
            "CGLS_NDVI1K_GLOBE_PROBAV_V301",
            "CGLS_NDVI1K_GLOBE_VGT_V301",
        ]
    ),
)
@click.option(
    "--output",
    "-o",
    "output_dir",
    type=click.Path(file_okay=False, dir_okay=True, writable=True, resolve_path=True),
    help="Output: directory",
)
@click.option(
    "--resolution",
    "-r",
    "resolution",
    type=click.Choice(["300m", "1km"]),
    default="1km",
    help="Resolution: target resolution, following what CGLS advertises: 300m, 1km",
)
@click.option(
    "--naming",
    "-n",
    "naming_pattern",
    type=click.STRING,
    default="_CGLS_NDVI_$(yyyy)_$(mm)_d$(mdekad)",
    help="Naming pattern; the following placeholders can be used: $(yyyy), $(mm), $(dd) and $(mdekad)",
)
@click.option(
    "--begin-date",
    "-b",
    "begin_date",
    type=click.DateTime(formats=["%Y-%m-%d"]),
    help="Start date: YYYY-MM-DD",
)
@click.option(
    "--end-date",
    "-e",
    "end_date",
    type=click.DateTime(formats=["%Y-%m-%d"]),
    help="End date: YYYY-MM-DD",
)
@click.option(
    "--aoi",
    "aoi",
    nargs=4,
    type=click.FLOAT,
    help="Area of Interest: [<UL lon>, <UL lat>, <LR lon>, <LR lat>. Example: --aoi -26.0 38.0 60.0 -35.0",
)
@click.option(
    "--local-mirror",
    "-m",
    "mirrors",
    type=click.Tuple([str, str, str]),
    multiple=True,
    help="""Path to mirror / pre-download per product; * for all. Examples:
      -m CGLS_NDVI300_GLOBE_OLCI_V201 /var/data/NDVI_300m_V2 rw
      -m * /var/data/CGLS_NDVI rw""",
)
@click.option(
    "--username",
    "-u",
    "username",
    type=click.STRING,
    help="Copernicus username",
)
@click.option(
    "--password",
    "-p",
    "password",
    type=click.STRING,
    help="Copernicus password",
)
@click.option(
    "--scratch",
    "-s",
    "scratch_dir",
    type=click.Path(file_okay=False, dir_okay=True, writable=True, resolve_path=True),
    help="""Path to temporary scratch dir""",
    default="",
)
def ingest(
    products: list[str],
    output_dir: str,
    resolution: str,
    naming_pattern: str,
    begin_date: datetime,
    end_date: datetime,
    aoi: tuple[float, float, float, float],
    mirrors: dict[str, tuple[Path, bool]],
    username: str,
    password: str,
    scratch_dir,
):
    mirrors = {t[0]: (Path(t[1]), t[2] != "rw") for t in mirrors}
    scratch_dir = Path(tempfile.gettempdir()) if len(scratch_dir) == 0 else Path(scratch_dir)

    assimilator = CGLSProductAssimilator(
        resolution, aoi, Path(output_dir), naming_pattern, begin_date, end_date, username, password
    )
    for product in products:
        # Setup a product accessors for each selected product:
        if product in mirrors:
            assimilator.add(__products[product], mirrors[product][0], mirrors[product][1])
        elif "*" in mirrors:
            assimilator.add(__products[product], mirrors["*"][0], mirrors["*"][1])
        else:
            assimilator.add(__products[product], None)

    if not assimilator.prepare():
        raise RuntimeError()
    assimilator.ingest()


def cli_wrap():
    """Wrapper for cli"""

    if len(sys.argv) == 1:
        ingest.main(["--help"])
    else:
        ingest()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s"
    )
    cli_wrap()
