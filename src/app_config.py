import os
from datetime import datetime

class AppConfig:
    def __init__(self):
        self.stac_url = os.getenv("STAC_URL", "https://earth-search.aws.element84.com/v1")
        self.open_street_maps = os.getenv("OSM_BASEMAP", "https://tile.openstreetmap.org/{z}/{x}/{y}.png")
        self.google_basemap = os.getenv("GOOGLE_BASEMAP", "https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}")
        self.esri_basemap = os.getenv("ESRI_BASEMAP", "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}")
        self.buffer_width = int(os.getenv("BUFFER_WIDTH", "3000"))
        self.geocoder_url = os.getenv("GEOCODER_API_URL", "https://nominatim.openstreetmap.org/search")
        self.geocoder_api_key = os.getenv("GEOCODER_API_KEY", "abcd")
        self.default_start_address = os.getenv("DEFAULT_START_ADDRESS", "San Francisco CA")
        self.enable_sentinel = os.getenv("ENABLE_SENTINEL", "True").lower() in ('true', '1', 't')
        self.enable_landsat = os.getenv("ENABLE_LANDSAT", "False").lower() in ('true', '1', 't')
        self.satelites = self.__get_satellites_params()
        self.default_cloud_cover = float(os.getenv("DEFAULT_CLOUD_COVER", "20.0"))
        self.default_satellite_choice_index = int(os.getenv("DEFAULT_SATELLITE_CHOICE_INDEX", "0"))
        self.max_stac_items = int(os.getenv("MAX_STAC_ITEMS", "5"))
        self.gif_default_time_per_image = float(os.getenv("GIF_DEFAULT_TIME_PER_IMAGE", "0.2"))
        self.gif_default_day_interval = int(os.getenv("GIF_DEFAULT_DAY_INTERVAL", "60"))
        self.allowed_gif_satellite = os.getenv("ALLOWED_GIF_SATELLITE", "sentinel 2").lower()
        self.max_saturation = float(os.getenv("IMAGE_MAX_SATURATION", 5))
        self.max_gamma = float(os.getenv("IMAGE_MAX_GAMMA", 5))
        self.max_sigmoidal = float(os.getenv("IMAGE_MAX_SIGMOIDAL", 15))
        self.max_sigmoidal_gain = float(os.getenv("IMAGE_MAX_SIGMOIDAL_GAIN", 5))

    def __get_satellites_params(self):
        params = {}
        if self.enable_sentinel:
            params.update({"Sentinel 2": self.__get_sensor_sentinel_params()})
        if self.enable_landsat:
            params.update({"Landsat": self.__get_sensor_landsat_params()})
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
        nir = os.getenv("SENTINEL_NIR_CHANNEL_ASSET_NAME", "nir")
        red = os.getenv("SENTINEL_R_CHANNEL_ASSET_NAME", "red")
        green = os.getenv("SENTINEL_G_CHANNEL_ASSET_NAME", "green")
        blue = os.getenv("SENTINEL_B_CHANNEL_ASSET_NAME", "blue")
        color_formula_sigmoidal = float(os.getenv("SENTINEL_COLOR_FORMULA_SIGMOIDAL", "6"))
        color_formula_sigmoidal_gain = float(os.getenv("SENTINEL_COLOR_FORMULA_SIGMOIDAL_GAIN", "0.1"))
        color_formula_gamma = float(os.getenv("SENTINEL_COLOR_FORMULA_GAMMA", "1.2"))
        color_formula_saturation = float(os.getenv("SENTINEL_COLOR_FORMULA_SATURATION", "2.3"))
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
            },
            "expression": {
                "ndvi": f"({nir}-{red})/({nir}+{red})",
                "ndwi": f"({red}-{nir})/({red}+{nir})",
                "evi": f"2.5*(({nir}-{red})/(({nir}-6*{red}-7.5*{blue})+1))",
                "savi": f"(({nir}-{red})/({nir}+{red}+0.5))*1.5"
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
        index_min_value = float(os.getenv("LANDSAT_INDEX_MIN_VALUE", -1))
        index_max_value = float(os.getenv("LANDSAT_INDEX_MAX_VALUE", 1))
        nir = os.getenv("LANDSAT_NIR_CHANNEL_ASSET_NAME", "nir08")
        red = os.getenv("LANDSAT_R_CHANNEL_ASSET_NAME", "red")
        green = os.getenv("LANDSAT_G_CHANNEL_ASSET_NAME", "green")
        blue = os.getenv("LANDSAT_B_CHANNEL_ASSET_NAME", "blue")
        color_formula_sigmoidal = float(os.getenv("LANDSAT_COLOR_FORMULA_SIGMOIDAL", "10"))
        color_formula_sigmoidal_gain = float(os.getenv("LANDSAT_COLOR_FORMULA_SIGMOIDAL_GAIN", "0.01"))
        color_formula_gamma = float(os.getenv("LANDSAT_COLOR_FORMULA_GAMMA", "1.2"))
        color_formula_saturation = float(os.getenv("LANDSAT_COLOR_FORMULA_SATURATION", "2.3"))
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
            },
            "expression": {
                "ndvi": f"({nir}-{red})/({nir}+{red})",
                "ndwi": f"({red}-{nir})/({red}+{nir})",
                "evi": f"2.5*(({nir}-{red})/(({nir}-6*{red}-7.5*{blue})+1))",
                "savi": f"(({nir}-{red})/({nir}+{red}+0.5))*1.5"
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
