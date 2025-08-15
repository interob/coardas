COARDAS
=======

The **CO**pernicus **A**nalysis **R**eady **D**ata **AS**ssimilation toolkit --COARDAS-- offers a command line utility for assimilating available datasets in the Copernicus Global Land Service (CGLS). The toolkit is designed to run with local access to the data (e.g. on the TerraScope platform (https://remotesensing.vito.be/case/terrascope), but the toolkit can also fallback to downloading the data to a local machine.

COARDAS' discrete resampling is based on and compatible with the routines that have been drafted and published by CGLS: https://github.com/cgls/ResampleTool_notebook_Python

Command: ingest
------
The script `ingest` concatenates available archives of compatible datasets into a single time series. For example:
- 1km SPOT/PROBA-V NDVI
- 300m Sentinel 3 OLCI NDVI

```
python ./coardas/ingest.py \
  CGLS_NDVI300_GLOBE_OLCI_V201 CGLS_NDVI1K_GLOBE_PROBAV_V301 CGLS_NDVI1K_GLOBE_VGT_V301 \
    -o ./data/copernicus-ndvi-1km -r 1km \
    -n 'CGLS_NDVI_1km_$(yyyy)_$(mm)_d$(mdekad)' \
    -b 1999-01-01 -e 2025-08-01 \
    --aoi -26.0 38.0 60.0 -35.0 \
    -m CGLS_NDVI300_GLOBE_OLCI_V201 /mirror/ndvi/ndvi_300m_v2_10daily r \
    -m CGLS_NDVI1K_GLOBE_PROBAV_V301 /mirror/ndvi/ndvi_1km_v3_10daily r \
    -m CGLS_NDVI1K_GLOBE_VGT_V301 /mirror/ndvi/ndvi_1km_v3_10daily r \
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

License & Warranty
------------------

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
