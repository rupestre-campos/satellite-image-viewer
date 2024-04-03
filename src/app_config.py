import os
from datetime import datetime

class AppConfig:
    def __init__(self):
        self.stac_url = os.getenv("STAC_URL", "https://earth-search.aws.element84.com/v1")
        self.open_street_maps = os.getenv("OSM_BASEMAP", "https://tile.openstreetmap.org/{z}/{x}/{y}.png")
        self.google_basemap = os.getenv("GOOGLE_BASEMAP", "https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}")
        self.esri_basemap = os.getenv("ESRI_BASEMAP", "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}")
        self.buffer_width = int(os.getenv("BUFFER_WIDTH", "3000"))
        self.email = os.getenv("EMAIL_NOMINATIM", "test-satellite-viewer@null.com")
        self.geocoder_user_agent = f"satellite-image-viewer+{self.email}"
        self.default_start_address = os.getenv("DEFAULT_START_ADDRESS", "Ingaí MG")
        self.enable_sentinel = os.getenv("ENABLE_SENTINEL", "True").lower() in ('true', '1', 't')
        self.enable_landsat = os.getenv("ENABLE_LANDSAT", "True").lower() in ('true', '1', 't')
        self.satelites = self.__get_satellites_params()
        self.default_cloud_cover = float(os.getenv("DEFAULT_CLOUD_COVER", "30.0"))
        self.default_satellite_choice_index = int(os.getenv("DEFAULT_SATELLITE_CHOICE_INDEX", "0"))


    def __get_satellites_params(self):
        params = {}
        if self.enable_sentinel:
            params.update({"sentinel 2": self.__get_sensor_sentinel_params()})
        if self.enable_landsat:
            params.update({"landsat": self.__get_sensor_landsat_params()})
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
        red_channel_asset_name = os.getenv("SENTINEL_R_CHANNEL_ASSET_NAME", "red")
        green_channel_asset_name = os.getenv("SENTINEL_G_CHANNEL_ASSET_NAME", "green")
        blue_channel_asset_name = os.getenv("SENTINEL_B_CHANNEL_ASSET_NAME", "blue")
        color_formula_sigmoidal = os.getenv("SENTINEL_COLOR_FORMULA_SIGMOIDAL", "sigmoidal RGB 6 0.1")
        color_formula_gamma = os.getenv("SENTINEL_COLOR_FORMULA_GAMMA", "gamma G 1.1 gamma B 1.2")
        color_formula_saturation = os.getenv("SENTINEL_COLOR_FORMULA_SATURATION", "saturation 1.2")
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
            "assets": (
                red_channel_asset_name,
                green_channel_asset_name,
                blue_channel_asset_name
            ),
            "color_formula":f"{color_formula_sigmoidal} {color_formula_gamma} {color_formula_saturation}",
            "aws_access_key_id": aws_access_key_id,
            "aws_secret_access_key": aws_secret_access_key,
            "aws_region_name": region_name,
            "aws_request_payer": aws_request_payer,
            "aws_no_sign_requests": aws_no_sign_requests
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
        red_channel_asset_name = os.getenv("LANDSAT_R_CHANNEL_ASSET_NAME", "red")
        green_channel_asset_name = os.getenv("LANDSAT_G_CHANNEL_ASSET_NAME", "green")
        blue_channel_asset_name = os.getenv("LANDSAT_B_CHANNEL_ASSET_NAME", "blue")
        color_formula_sigmoidal = os.getenv("LANDSAT_COLOR_FORMULA_SIGMOIDAL", "sigmoidal RGB 10 0.01")
        color_formula_gamma = os.getenv("LANDSAT_COLOR_FORMULA_GAMMA", "gamma G 1.1 gamma B 1.2")
        color_formula_saturation = os.getenv("LANDSAT_COLOR_FORMULA_SATURATION", "saturation 1.2")
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
            "assets": (
                red_channel_asset_name,
                green_channel_asset_name,
                blue_channel_asset_name
            ),
            "color_formula":f"{color_formula_sigmoidal} {color_formula_gamma} {color_formula_saturation}",
            "aws_access_key_id": aws_access_key_id,
            "aws_secret_access_key": aws_secret_access_key,
            "aws_region_name": region_name,
            "aws_request_payer": aws_request_payer,
            "aws_no_sign_requests": aws_no_sign_requests
        }
