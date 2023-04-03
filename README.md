COARDAS
=======

The **CO**pernicus **A**nalysis **R**eady **D**ata **AS**ssimilation toolkit --COARDAS-- offers a command line utility for assimilating available Copernicus datasets. The toolkit is designed to run with local access to the data (e.g. on the TerraScope platform (https://remotesensing.vito.be/case/terrascope), but the toolkit can also fallback to downloading the data to a local machine.

Command: ingest
------
The script `ingest` concatenates available archives of compatible datasets into a single time series. For example:
- 1km SPOT/PROBA-V NDVI
- 300m Sentinel 3 OLCI NDVI

```
ingest.py CGLS_NDVI300_GLOBE_OLCI_V201 CGLS_NDVI1K_GLOBE_PROBAV_V301 \
    -o ./data/copernicus-ndvi-1km -r 1km \
    -n "CGLS_NDVI_1km_$(yyyy)_$(mm)_d$(mdekad)" \
    -b "2020-06-21" -e 2020-07-01 \
    --aoi -26.0 38.0 60.0 -35.0 \
    -m CGLS_NDVI300_GLOBE_OLCI_V201 ./data/NDVI_300m_V2 r \
    -m CGLS_NDVI1K_GLOBE_PROBAV_V301 ./data/NDVI_1km_V3 r \
    -u <your copernicus username> -p <your copernicus password> \
    -s /var/tmp
```

Installation
------------
**Dependencies:**

COARDAS depends on these packages:

- numpy
- gdal
- tqdm
- xarray
- rasterio
- requests
- click

Some of these packages (eg. GDAL) can be difficult to build, especially on windows machines. In the latter case it's advisable to download an unofficial binary wheel from `Christoph Gohlke's Unofficial Windows Binaries for Python Extension Packages <https://www.lfd.uci.edu/~gohlke/pythonlibs/>`_ and install it locally with ``pip install`` before installing COARDAS.

**Installation from github:**


    $ git clone https://github.com/interob/coardas
    $ cd coardas
    $ pip3 install .
