"""
Product classes for products in the Copernicus Global Land Service (CGLS) programme.

Author: Rob Marjot, March 2023
"""
from pathlib import Path

import xarray as xr

from coardas.cgls.translator import CGLSResamplingTranslator, CGLSTranslator


class CGLSProduct:
    def __init__(
        self,
        *,
        variable: str,
        manifest: str,
        patn_manifest: str,
        patn_datafile: str,
        patn_metadata: str,
        resolution: str,
    ) -> None:
        self.__variable = variable
        self.__manifest = manifest
        self.__patn_manifest = patn_manifest
        self.__patn_datafile = patn_datafile
        self.__patn_metadata = patn_metadata
        self.__resolution = resolution

    @property
    def manifest_url(self):
        return self.__manifest
    
    @property
    def patn_manifest(self):
        return self.__patn_manifest

    @property
    def patn_datafile(self):
        return self.__patn_datafile

    @property
    def patn_metadata(self):
        return self.__patn_metadata

    @property
    def variable(self):
        return self.__variable

    @property
    def resolution(self):
        return self.__resolution

    def get_translator(
        self, datafile: Path, variable: str, target_resolution: str
    ) -> CGLSTranslator:
        """
        Factory returning the appropriate translator needed for assimilating the product's datafile
        into into the composite series with the indicated target_resolution.

        :param target_resolution = "1km", "300m"
        """
        product_pixels_per_degree = CGLSTranslator.pixels_per_degree(self.resolution)
        target_pixels_per_degree = CGLSTranslator.pixels_per_degree(target_resolution)

        if (product_pixels_per_degree % target_pixels_per_degree) != 0:
            raise RuntimeError()
        else:
            with xr.open_dataset(datafile.as_posix(), mask_and_scale=False) as ds:
                ds: xr.Dataset
                gt = tuple(float(f) for f in str(ds["crs"].attrs["GeoTransform"]).split())
                shape = ds[variable].shape
                if product_pixels_per_degree == target_pixels_per_degree:
                    return CGLSTranslator(
                        gt,
                        (shape[1], shape[2]),
                        list(ds.coords["lat"].values),
                        list(ds.coords["lon"].values),
                        product_pixels_per_degree,
                        ds[variable].attrs["scale_factor"],
                        ds[variable].attrs["add_offset"],
                        int(ds[variable].attrs["_FillValue"]),
                    )
                else:
                    return CGLSResamplingTranslator(
                        gt,
                        (shape[1], shape[2]),
                        list(ds.coords["lat"].values),
                        list(ds.coords["lon"].values),
                        product_pixels_per_degree,
                        target_pixels_per_degree,
                        ds[variable].attrs["scale_factor"],
                        ds[variable].attrs["add_offset"],
                        int(ds[variable].attrs["_FillValue"]),
                    )


manifest_baseurl = "https://land.copernicus.vgt.vito.be/manifest"
# datapool_veg_baseurl = "https://land.copernicus.vgt.vito.be/PDF/datapool/Vegetation/Indicators"

CGLS_NDVI300_GLOBE_OLCI_V201 = CGLSProduct(
    **{
        "variable": "NDVI",
        "manifest": f"{manifest_baseurl}/ndvi300_v2_333m/manifest_cgls_ndvi300_v2_333m_latest.txt",
        "patn_manifest": "$(yyyy)/$(mm)/$(dd)/NDVI300_$(yyyy)$(mm)$(dd)0000_GLOBE_OLCI_V2.0.1/c_gls_NDVI300_$(yyyy)$(mm)$(dd)0000_GLOBE_OLCI_V2.0.1.nc",
        "patn_datafile": "$(yyyy)/$(yyyy)$(mm)$(dd)/c_gls_NDVI300_$(yyyy)$(mm)$(dd)0000_GLOBE_OLCI_V2.0.1.nc",
        # {datapool_veg_baseurl}/NDVI_300m_V2/
        "patn_metadata": "$(yyyy)/$(mm)/$(dd)/NDVI300_$(yyyy)$(mm)$(dd)0000_GLOBE_OLCI_V2.0.1/c_gls_NDVI300_PROD-DESC_$(yyyy)$(mm)$(dd)0000_GLOBE_OLCI_V2.0.1.xml",
        "resolution": "300m",
    }
)

CGLS_NDVI1K_GLOBE_PROBAV_V301 = CGLSProduct(
    **{
        "variable": "NDVI",
        "manifest": f"{manifest_baseurl}/ndvi_v3_1km/manifest_cgls_ndvi_v3_1km_latest.txt",
        "patn_manifest": "$(yyyy)/$(mm)/$(dd)/NDVI_$(yyyy)$(mm)$(dd)0000_GLOBE_PROBAV_V3.0.1/c_gls_NDVI_$(yyyy)$(mm)$(dd)0000_GLOBE_PROBAV_V3.0.1.nc",
        "patn_datafile": "$(yyyy)/$(yyyy)$(mm)$(dd)/c_gls_NDVI_$(yyyy)$(mm)$(dd)0000_GLOBE_PROBAV_V3.0.1.nc",
        # {datapool_veg_baseurl}/NDVI_1km_V3/
        "patn_metadata": "$(yyyy)/$(mm)/$(dd)/NDVI_$(yyyy)$(mm)$(dd)0000_GLOBE_PROBAV_V3.0.1/c_gls_NDVI_$(yyyy)$(mm)$(dd)0000_GLOBE_PROBAV_V3.0.1.xml",
        "resolution": "1km",
    }
)

CGLS_NDVI1K_GLOBE_VGT_V301 = CGLSProduct(
    **{
        "variable": "NDVI",
        "manifest": f"{manifest_baseurl}/ndvi_v3_1km/manifest_cgls_ndvi_v3_1km_latest.txt",
        "patn_manifest": "$(yyyy)/$(mm)/$(dd)/NDVI_$(yyyy)$(mm)$(dd)0000_GLOBE_VGT_V3.0.1/c_gls_NDVI_$(yyyy)$(mm)$(dd)0000_GLOBE_VGT_V3.0.1.nc",
        "patn_datafile": "$(yyyy)/$(yyyy)$(mm)$(dd)/c_gls_NDVI_$(yyyy)$(mm)$(dd)0000_GLOBE_VGT_V3.0.1.nc",
        # {datapool_veg_baseurl}/NDVI_1km_V3/
        "patn_metadata": "$(yyyy)/$(mm)/$(dd)/NDVI_$(yyyy)$(mm)$(dd)0000_GLOBE_VGT_V3.0.1/c_gls_NDVI_$(yyyy)$(mm)$(dd)0000_GLOBE_VGT_V3.0.1.xml",
        "resolution": "1km",
    }
)

#     def _param(ds: xr.Dataset) -> Tuple[xr.DataArray, Dict[str, Union[str, int, float]]]:
#         """
#         Select parameters according to the product.
#         """

#         if "LAI" in ds.data_vars:
#             return ds.LAI, {
#                 "product": "LAI",
#                 "short_name": "leaf_area_index",
#                 "long_name": "Leaf Area Index Resampled 1 Km",
#                 "grid_mapping": "crs",
#                 "flag_meanings": "Missing",
#                 "flag_values": "255",
#                 "units": "",
#                 "PHYSICAL_MIN": 0,
#                 "PHYSICAL_MAX": 7,
#                 "DIGITAL_MAX": 210,
#                 "SCALING": 1.0 / 30,
#                 "OFFSET": 0,
#             }

#         if "FCOVER" in ds.data_vars:
#             return ds.FCOVER, {
#                 "product": "FCOVER",
#                 "short_name": "vegetation_area_fraction",
#                 "long_name": "Fraction of green Vegetation Cover Resampled 1 Km",
#                 "grid_mapping": "crs",
#                 "flag_meanings": "Missing",
#                 "flag_values": "255",
#                 "units": "",
#                 "valid_range": "",
#                 "PHYSICAL_MIN": 0,
#                 "PHYSICAL_MAX": 1.0,
#                 "DIGITAL_MAX": 250,
#                 "SCALING": 1.0 / 250,
#                 "OFFSET": 0,
#             }

#         if "FAPAR" in ds.data_vars:
#             return ds.FAPAR, {
#                 "product": "FAPAR",
#                 "short_name": "Fraction_of_Absorbed_Photosynthetically_Active_Radiation",
#                 "long_name": "Fraction of Absorbed Photosynthetically Active Radiation Resampled 1 KM",
#                 "grid_mapping": "crs",
#                 "flag_meanings": "Missing",
#                 "flag_values": "255",
#                 "units": "",
#                 "valid_range": "",
#                 "PHYSICAL_MIN": 0,
#                 "PHYSICAL_MAX": 0.94,
#                 "DIGITAL_MAX": 235,
#                 "SCALING": 1.0 / 250,
#                 "OFFSET": 0,
#             }

#         if "NDVI" in ds.data_vars:
#             return ds.NDVI, {
#                 "product": "NDVI",
#                 "short_name": "Normalized_difference_vegetation_index",
#                 "long_name": "Normalized Difference Vegetation Index Resampled 1 Km",
#                 "grid_mapping": "crs",
#                 "flag_meanings": "Missing cloud snow sea background",
#                 "flag_values": "[251 252 253 254 255]",
#                 "units": "",
#                 "PHYSICAL_MIN": -0.08,
#                 "PHYSICAL_MAX": 0.92,
#                 "DIGITAL_MAX": 250,
#                 "SCALING": 1.0 / 250,
#                 "OFFSET": -0.08,
#             }

#         if "DMP" in ds.data_vars:
#             return ds.DMP, {
#                 "product": "DMP",
#                 "short_name": "dry_matter_productivity",
#                 "long_name": "Dry matter productivity Resampled 1KM",
#                 "grid_mapping": "crs",
#                 "flag_meanings": "sea",
#                 "flag_values": "-2",
#                 "units": "kg / ha / day",
#                 "PHYSICAL_MIN": 0,
#                 "PHYSICAL_MAX": 327.67,
#                 "DIGITAL_MAX": 32767,
#                 "SCALING": 1.0 / 100,
#                 "OFFSET": 0,
#             }

#         if "GDMP" in ds.data_vars:
#             return ds.GDMP, {
#                 "product": "GDMP",
#                 "short_name": "Gross_dry_matter_productivity",
#                 "long_name": "Gross dry matter productivity Resampled 1KM",
#                 "grid_mapping": "crs",
#                 "flag_meanings": "sea",
#                 "flag_values": "-2",
#                 "units": "kg / hectare / day",
#                 "PHYSICAL_MIN": 0,
#                 "PHYSICAL_MAX": 655.34,
#                 "DIGITAL_MAX": 32767,
#                 "SCALING": 1.0 / 50,
#                 "OFFSET": 0,
#             }
