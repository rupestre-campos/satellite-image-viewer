import os
from datetime import datetime

class AppConfig:
    def __init__(self):
        self.stac_url = os.getenv("STAC_URL", "https://earth-search.aws.element84.com/v1")
        self.open_street_maps = os.getenv("OSM_BASEMAP", "https://tile.openstreetmap.org/{z}/{x}/{y}.png")
        self.google_basemap = os.getenv("GOOGLE_BASEMAP", "https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}")
        self.esri_basemap = os.getenv("ESRI_BASEMAP", "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}")
        self.buffer_width = int(os.getenv("BUFFER_WIDTH", "3000"))
        self.buffer_max_width = int(os.getenv("BUFFER_MAX_WIDTH", "3000"))
        self.float_precision = int(os.getenv("FLOAT_PRECISION", 6))
        self.geocoder_url = os.getenv("GEOCODER_API_URL", "https://nominatim.openstreetmap.org/search")
        self.geocoder_api_key = os.getenv("GEOCODER_API_KEY", "abcd")
        self.default_start_address = os.getenv("DEFAULT_START_ADDRESS", "San Francisco CA")
        self.address_max_chars = int(os.getenv("ADDRESS_MAX_CHARS", "128"))
        self.enable_sentinel = os.getenv("ENABLE_SENTINEL", "True").lower() in ('true', '1', 't')
        self.enable_sentinel1 = os.getenv("ENABLE_SENTINEL1", "False").lower() in ('true', '1', 't')
        self.enable_landsat = os.getenv("ENABLE_LANDSAT", "False").lower() in ('true', '1', 't')
        self.enable_dem = os.getenv("ENABLE_DEM", "False").lower() in ('true', '1', 't')
        self.satelites = self.__get_satellites_params()
        self.default_cloud_cover = float(os.getenv("DEFAULT_CLOUD_COVER", "20.0"))
        self.cloud_cover_step = float(os.getenv("CLOUD_COVER_STEP", "0.3"))
        self.default_satellite_choice_index = int(os.getenv("DEFAULT_SATELLITE_CHOICE_INDEX", "0"))
        self.max_stac_items = int(os.getenv("MAX_STAC_ITEMS", "5"))
        self.gif_min_time_per_image = float(os.getenv("GIF_MIN_TIME_PER_IMAGE_SEC", "0.1"))
        self.gif_default_time_per_image = float(os.getenv("GIF_DEFAULT_TIME_PER_IMAGE_SEC", "0.3"))
        self.gif_max_time_per_image = float(os.getenv("GIF_MAX_TIME_PER_IMAGE", "5"))
        self.gif_max_img_size = int(os.getenv("GIF_MAX_IMG_SIZE_PIXELS", "512"))
        self.gif_default_img_size = int(os.getenv("GIF_DEFAULT_IMG_SIZE_PIXELS", "320"))
        self.gif_min_img_size = int(os.getenv("GIF_MIN_IMG_SIZE_PIXELS", "10"))
        self.gif_min_interval = int(os.getenv("GIF_MIN_INTERVAL_DAYS", "4"))
        self.gif_default_interval = int(os.getenv("GIF_DEFAULT_INTERVAL_DAYS", "120"))
        self.gif_max_interval = int(os.getenv("GIF_MAX_INTERVAL_DAYS", "365"))
        self.allowed_gif_satellite = os.getenv("ALLOWED_GIF_SATELLITE", "sentinel 2").lower()
        self.max_saturation = float(os.getenv("IMAGE_MAX_SATURATION", 100))
        self.max_gamma = float(os.getenv("IMAGE_MAX_GAMMA", 100))
        self.max_sigmoidal = float(os.getenv("IMAGE_MAX_SIGMOIDAL", 100))
        self.max_sigmoidal_gain = float(os.getenv("IMAGE_MAX_SIGMOIDAL_GAIN", 1))
        self.default_composition_index = int(os.getenv("DEFAULT_COMPOSITION_INDEX", 0))
        self.default_composition_value_for_index = os.getenv("DEFAULT_COMPOSITION_VALUE_INDEX", "ndvi")
        self.default_composition_value_for_composite = os.getenv("DEFAULT_COMPOSITION_VALUE_COMPOSITE", "real-color (RGB)")
        self.enhance_image_default = os.getenv("DEFAULT_ENHANCE_IMAGE", "False").lower() in ('true', '1', 't')
        self.enhance_image_passes = os.getenv("ENHANCE_IMAGE_PASSES", "1,2")

    def __get_satellites_params(self):
        params = {}
        if self.enable_sentinel:
            params.update({"Sentinel 2": self.__get_sensor_sentinel_params()})
        if self.enable_landsat:
            params.update({"Landsat": self.__get_sensor_landsat_params()})
        if self.enable_sentinel1:
            params.update({"Sentinel 1": self.__get_sensor_sentinel1_params()})
        if self.enable_dem:
            params.update({"Copernicus DEM": self.__get_copernicus_dem_params()})
        return params

    @staticmethod
    def __get_sensor_sentinel_params():
        collection_name = os.getenv("SENTINEL_COLLECTION_NAME", "sentinel-2-l2a")
        collection_start_date = os.getenv("SENTINEL_COLLECTION_START_DATE", "2015-06-23")
        collection_end_date = os.getenv("SENTINEL_COLLECTION_END_DATE", datetime.now().strftime("%Y-%m-%d"))
        image_max_size = os.getenv("SENTINEL_IMAGE_MAX_SIZE", None)
        band_nodata_value = int(os.getenv("SENTINEL_BAND_NODATA_VALUE", 0))
        band_min_value = int(os.getenv("SENTINEL_BAND_MIN_VALUE", 0))
        band_max_value = int(os.getenv("SENTINEL_BAND_MAX_VALUE", 4000))
        index_min_value = float(os.getenv("SENTINEL_INDEX_MIN_VALUE", -1))
        index_max_value = float(os.getenv("SENTINEL_INDEX_MAX_VALUE", 1))
        coastal = os.getenv("SENTINEL_COASTAL_CHANNEL_ASSET_NAME", "nir")
        nir = os.getenv("SENTINEL_NIR_CHANNEL_ASSET_NAME", "nir")
        red = os.getenv("SENTINEL_R_CHANNEL_ASSET_NAME", "red")
        green = os.getenv("SENTINEL_G_CHANNEL_ASSET_NAME", "green")
        blue = os.getenv("SENTINEL_B_CHANNEL_ASSET_NAME", "blue")
        nir08 = os.getenv("SENTINEL_NIR08_CHANNEL_ASSET_NAME", "nir08")
        swir16 = os.getenv("SENTINEL_SWIR16_CHANNEL_ASSET_NAME", "swir16")
        swir22 = os.getenv("SENTINEL_SWIR22_CHANNEL_ASSET_NAME", "swir22")
        color_formula_sigmoidal = float(os.getenv("SENTINEL_COLOR_FORMULA_SIGMOIDAL", "5"))
        color_formula_sigmoidal_gain = float(os.getenv("SENTINEL_COLOR_FORMULA_SIGMOIDAL_GAIN", "0.1"))
        color_formula_gamma = float(os.getenv("SENTINEL_COLOR_FORMULA_GAMMA", "1.2"))
        color_formula_saturation = float(os.getenv("SENTINEL_COLOR_FORMULA_SATURATION", "1.2"))
        aws_access_key_id = os.getenv("SENTINEL_AWS_ACCESS_KEY_ID", "")
        aws_secret_access_key = os.getenv("SENTINEL_AWS_SECRET_ACCESS_KEY", "")
        region_name = os.getenv("SENTINEL_AWS_REGION_NAME", "us-west-2")
        aws_request_payer = os.getenv("SENTINEL_AWS_REQUEST_PAYER", "provider")
        aws_no_sign_requests = os.getenv("SENTINEL_AWS_NO_SIGN_REQUESTS", "NO")
        platforms = os.getenv("SENTINEL_PLATFORMS", "")

        return {
            "name": "Sentinel 2",
            "collection_name": collection_name,
            "start_date": collection_start_date,
            "end_date": collection_end_date,
            "min_value": band_min_value,
            "max_value": band_max_value,
            "nodata": band_nodata_value,
            "max_size": image_max_size,
            "platforms": platforms,
            "assets": {
                "real-color (RGB)": (
                    red,
                    green,
                    blue
                ),
                "vegetation (NirRG)": (
                    nir,
                    red,
                    green
                ),
                "agriculture (SwirNirB)": (
                    swir16,
                    nir,
                    blue
                ),
                "geology": (
                    swir22,
                    swir16,
                    blue
                ),
                "thermal (SWIR)": (
                    swir22,
                    nir08,
                    red
                ),
                "bathymetry": (
                    red,
                    green,
                    coastal
                )
            },
            "expression": {
                "ndvi": f"({nir}-{red})/({nir}+{red})",
                "ndwi": f"({red}-{nir})/({red}+{nir})",
                "evi": f"2.5*(({nir}-{red})/(({nir}-6*{red}-7.5*{blue})+1))",
                "savi": f"(({nir}-{red})/({nir}+{red}+0.5))*1.5",
                "nbr": f"({nir}-{swir22})/({nir}+{swir22})"
            },
            "index_min_value": index_min_value,
            "index_max_value": index_max_value,
            "color_formula":
                f"sigmoidal RGB {color_formula_sigmoidal} {color_formula_sigmoidal_gain} "\
                f"gamma RGB {color_formula_gamma} "\
                f"saturation {color_formula_saturation}",
            "aws_access_key_id": aws_access_key_id,
            "aws_secret_access_key": aws_secret_access_key,
            "aws_region_name": region_name,
            "aws_request_payer": aws_request_payer,
            "aws_no_sign_requests": aws_no_sign_requests,
            "color_formula_saturation": color_formula_saturation,
            "color_formula_sigmoidal": color_formula_sigmoidal,
            "color_formula_sigmoidal_gain": color_formula_sigmoidal_gain,
            "color_formula_gamma": color_formula_gamma,
        }

    @staticmethod
    def __get_sensor_landsat_params():
        collection_name = os.getenv("LANDSAT_COLLECTION_NAME", "landsat-c2-l2")
        collection_start_date = os.getenv("LANDSAT_COLLECTION_START_DATE", "1982-07-16")
        collection_end_date = os.getenv("LANDSAT_COLLECTION_END_DATE", datetime.now().strftime("%Y-%m-%d"))
        image_max_size = os.getenv("LANDSAT_IMAGE_MAX_SIZE", None)
        band_nodata_value = int(os.getenv("LANDSAT_BAND_NODATA_VALUE", 0))
        band_min_value = int(os.getenv("LANDSAT_BAND_MIN_VALUE", 7273))
        band_max_value = int(os.getenv("LANDSAT_BAND_MAX_VALUE", 43636))
        index_min_value = float(os.getenv("LANDSAT_INDEX_MIN_VALUE", -0.5))
        index_max_value = float(os.getenv("LANDSAT_INDEX_MAX_VALUE", 0.5))
        nir = os.getenv("LANDSAT_NIR_CHANNEL_ASSET_NAME", "nir08")
        red = os.getenv("LANDSAT_R_CHANNEL_ASSET_NAME", "red")
        green = os.getenv("LANDSAT_G_CHANNEL_ASSET_NAME", "green")
        blue = os.getenv("LANDSAT_B_CHANNEL_ASSET_NAME", "blue")
        swir16 = os.getenv("LANDSAT_SWIR16_CHANNEL_ASSET_NAME", "swir16")
        swir22 = os.getenv("LANDSAT_SWIR22_CHANNEL_ASSET_NAME", "swir22")
        color_formula_sigmoidal = float(os.getenv("LANDSAT_COLOR_FORMULA_SIGMOIDAL", "10"))
        color_formula_sigmoidal_gain = float(os.getenv("LANDSAT_COLOR_FORMULA_SIGMOIDAL_GAIN", "0.01"))
        color_formula_gamma = float(os.getenv("LANDSAT_COLOR_FORMULA_GAMMA", "1.4"))
        color_formula_saturation = float(os.getenv("LANDSAT_COLOR_FORMULA_SATURATION", "1.2"))
        aws_access_key_id = os.getenv("LANDSAT_AWS_ACCESS_KEY_ID", "")
        aws_secret_access_key = os.getenv("LANDSAT_AWS_SECRET_ACCESS_KEY", "")
        region_name = os.getenv("LANDSAT_AWS_REGION_NAME", "us-west-2")
        aws_request_payer = os.getenv("LANDSAT_AWS_REQUEST_PAYER", "requester")
        aws_no_sign_requests = os.getenv("LANDSAT_AWS_NO_SIGN_REQUESTS", "NO")
        platforms = os.getenv("LANDSAT_PLATFORMS", "landsat-4,landsat-5,landsat-8,landsat-9").split(",")

        return {
            "name": "Landsat",
            "collection_name": collection_name,
            "start_date": collection_start_date,
            "end_date": collection_end_date,
            "min_value": band_min_value,
            "max_value": band_max_value,
            "nodata": band_nodata_value,
            "max_size": image_max_size,
            "platforms": platforms,
            "assets": {
                "real-color (RGB)": (
                    red,
                    green,
                    blue
                ),
                "vegetation (NirRG)": (
                    nir,
                    red,
                    green
                ),
                "agriculture (SwirNirB)": (
                    swir16,
                    nir,
                    blue
                ),
                "geology": (
                    swir22,
                    swir16,
                    blue
                ),
                "thermal (SWIR)": (
                    swir22,
                    nir,
                    red
                ),
                "bathymetry": (
                    nir,
                    green,
                    blue
                )
            },
            "expression": {
                "ndvi": f"({nir}-{red})/({nir}+{red})",
                "ndwi": f"({red}-{nir})/({red}+{nir})",
                "evi": f"2.5*(({nir}-{red})/(({nir}-6*{red}-7.5*{blue})+1))",
                "savi": f"(({nir}-{red})/({nir}+{red}+0.5))*1.5",
                "nbr": f"({nir}-{swir22})/({nir}+{swir22})"
            },
            "index_min_value": index_min_value,
            "index_max_value": index_max_value,
            "color_formula":
                f"sigmoidal RGB {color_formula_sigmoidal} {color_formula_sigmoidal_gain} "\
                f"gamma RGB {color_formula_gamma} "\
                f"saturation {color_formula_saturation}",
            "aws_access_key_id": aws_access_key_id,
            "aws_secret_access_key": aws_secret_access_key,
            "aws_region_name": region_name,
            "aws_request_payer": aws_request_payer,
            "aws_no_sign_requests": aws_no_sign_requests,
            "color_formula_saturation": color_formula_saturation,
            "color_formula_sigmoidal": color_formula_sigmoidal,
            "color_formula_sigmoidal_gain": color_formula_sigmoidal_gain,
            "color_formula_gamma": color_formula_gamma,
        }

    @staticmethod
    def __get_sensor_sentinel1_params():
        collection_name = os.getenv("SENTINEL1_COLLECTION_NAME", "sentinel-1-grd")
        collection_start_date = os.getenv("SENTINEL1_COLLECTION_START_DATE", "2014-10-10")
        collection_end_date = os.getenv("SENTINEL1_COLLECTION_END_DATE", datetime.now().strftime("%Y-%m-%d"))
        image_max_size = os.getenv("SENTINEL1_IMAGE_MAX_SIZE", None)
        band_nodata_value = int(os.getenv("SENTINEL1_BAND_NODATA_VALUE", 0))
        band_min_value = int(os.getenv("SENTINEL1_BAND_MIN_VALUE", 0))
        band_max_value = int(os.getenv("SENTINEL1_BAND_MAX_VALUE", 4000))
        index_min_value = float(os.getenv("SENTINEL1_INDEX_MIN_VALUE", -1))
        index_max_value = float(os.getenv("SENTINEL1_INDEX_MAX_VALUE", 4000))
        hh = os.getenv("SENTINEL1_HH_CHANNEL_ASSET_NAME", "hh")
        hv = os.getenv("SENTINEL1_HV_CHANNEL_ASSET_NAME", "hv")
        vh = os.getenv("SENTINEL1_VH_CHANNEL_ASSET_NAME", "vh")
        vv = os.getenv("SENTINEL1_VV_CHANNEL_ASSET_NAME", "vv")
        color_formula_sigmoidal = float(os.getenv("SENTINEL1_COLOR_FORMULA_SIGMOIDAL", "5"))
        color_formula_sigmoidal_gain = float(os.getenv("SENTINEL1_COLOR_FORMULA_SIGMOIDAL_GAIN", "0.1"))
        color_formula_gamma = float(os.getenv("SENTINEL1_COLOR_FORMULA_GAMMA", "1.2"))
        color_formula_saturation = float(os.getenv("SENTINEL1_COLOR_FORMULA_SATURATION", "1.2"))
        aws_access_key_id = os.getenv("SENTINEL1_AWS_ACCESS_KEY_ID", "")
        aws_secret_access_key = os.getenv("SENTINEL1_AWS_SECRET_ACCESS_KEY", "")
        region_name = os.getenv("SENTINEL1_AWS_REGION_NAME", "eu-central-1")
        aws_request_payer = os.getenv("SENTINEL1_AWS_REQUEST_PAYER", "provider")
        aws_no_sign_requests = os.getenv("SENTINEL1_AWS_NO_SIGN_REQUESTS", "NO")
        platforms = os.getenv("SENTINEL1_PLATFORMS", "")

        return {
            "name": "Sentinel 1",
            "collection_name": collection_name,
            "start_date": collection_start_date,
            "end_date": collection_end_date,
            "min_value": band_min_value,
            "max_value": band_max_value,
            "nodata": band_nodata_value,
            "max_size": image_max_size,
            "platforms": platforms,
            "assets": {
                "vv-vh-vv": (
                    vv,
                    vh,
                    vv
                ),
                "vv-vh-vh": (
                    vv,
                    vh,
                    vh
                ),
            },
            "expression": {
                "vv": f"{vv}",
                "vh": f"{vh}",
                "vv/vh": f"{vv}/{vh}",
                "swi": f"0.1747 * {vv} + 0.0082 * {vh} * {vv} + 0.0023 * {vv}**2 - 0.0015 * {vh}**2 + 0.1904"
            },
            "RGB-expression": {
                "vv|vh|vv/vh": {
                    "assets": (vv, vh),
                    "expression":f"{vv},{vh},{vv}/{vh}"
                },
                "vv-vh|vh-vv|vv/vh": {
                    "assets": (vv, vh),
                    "expression":f"{vv}-{vh},{vh}-{vv},{vv}/{vh}"
                }
            },
            "index_min_value": index_min_value,
            "index_max_value": index_max_value,
            "color_formula":
                f"sigmoidal RGB {color_formula_sigmoidal} {color_formula_sigmoidal_gain} "\
                f"gamma RGB {color_formula_gamma} "\
                f"saturation {color_formula_saturation}",
            "aws_access_key_id": aws_access_key_id,
            "aws_secret_access_key": aws_secret_access_key,
            "aws_region_name": region_name,
            "aws_request_payer": aws_request_payer,
            "aws_no_sign_requests": aws_no_sign_requests,
            "color_formula_saturation": color_formula_saturation,
            "color_formula_sigmoidal": color_formula_sigmoidal,
            "color_formula_sigmoidal_gain": color_formula_sigmoidal_gain,
            "color_formula_gamma": color_formula_gamma,
        }
    @staticmethod
    def __get_copernicus_dem_params():
        collection_name = os.getenv("DEM_COLLECTION_NAME", "cop-dem-glo-30")
        collection_start_date = os.getenv("DEM_COLLECTION_START_DATE", "2021-04-20")
        collection_end_date = os.getenv("DEM_COLLECTION_END_DATE", datetime.now().strftime("%Y-%m-%d"))
        image_max_size = os.getenv("DEM_IMAGE_MAX_SIZE", None)
        band_nodata_value = int(os.getenv("DEM_BAND_NODATA_VALUE", -10000))
        band_min_value = int(os.getenv("DEM_BAND_MIN_VALUE", 0))
        band_max_value = int(os.getenv("DEM_BAND_MAX_VALUE", 9000))
        index_min_value = float(os.getenv("DEM_INDEX_MIN_VALUE", 0))
        index_max_value = float(os.getenv("DEM_INDEX_MAX_VALUE", 9000))
        data = os.getenv("DEM_DATA_CHANNEL_ASSET_NAME", "data")
        color_formula_sigmoidal = float(os.getenv("DEM_COLOR_FORMULA_SIGMOIDAL", "10"))
        color_formula_sigmoidal_gain = float(os.getenv("DEM_COLOR_FORMULA_SIGMOIDAL_GAIN", "0.01"))
        color_formula_gamma = float(os.getenv("DEM_COLOR_FORMULA_GAMMA", "1.4"))
        color_formula_saturation = float(os.getenv("DEM_COLOR_FORMULA_SATURATION", "1.2"))
        aws_access_key_id = os.getenv("DEM_AWS_ACCESS_KEY_ID", "")
        aws_secret_access_key = os.getenv("DEM_AWS_SECRET_ACCESS_KEY", "")
        region_name = os.getenv("DEM_AWS_REGION_NAME", "eu-central-1")
        aws_request_payer = os.getenv("DEM_AWS_REQUEST_PAYER", "provider")
        aws_no_sign_requests = os.getenv("DEM_AWS_NO_SIGN_REQUESTS", "NO")
        platforms = os.getenv("DEM_PLATFORMS", "")

        return {
            "name": "Copernicus DEM",
            "collection_name": collection_name,
            "start_date": collection_start_date,
            "end_date": collection_end_date,
            "min_value": band_min_value,
            "max_value": band_max_value,
            "nodata": band_nodata_value,
            "max_size": image_max_size,
            "platforms": platforms,
            "expression": {
                "dem": f"{data}",
            },
            "index_min_value": index_min_value,
            "index_max_value": index_max_value,
            "color_formula":
                f"sigmoidal RGB {color_formula_sigmoidal} {color_formula_sigmoidal_gain} "\
                f"gamma RGB {color_formula_gamma} "\
                f"saturation {color_formula_saturation}",
            "aws_access_key_id": aws_access_key_id,
            "aws_secret_access_key": aws_secret_access_key,
            "aws_region_name": region_name,
            "aws_request_payer": aws_request_payer,
            "aws_no_sign_requests": aws_no_sign_requests,
            "color_formula_saturation": color_formula_saturation,
            "color_formula_sigmoidal": color_formula_sigmoidal,
            "color_formula_sigmoidal_gain": color_formula_sigmoidal_gain,
            "color_formula_gamma": color_formula_gamma,
        }