from controller.environment_variable_manager import EnvContextManager

from model.read_stac import ReadSTAC

class ImageRenderer:
    def __init__(self,):
        self.stac_reader = self.__model_read_stac()

    @staticmethod
    def __model_read_stac():
        return ReadSTAC()

    @staticmethod
    def __geojson_geometry_to_feature(geojson_geometry):
        return {
            "type": "Feature",
            "properties": {},
            "geometry": geojson_geometry
        }

    def render_mosaic_from_stac(self, params):
        geojson_geometry = params.get("geojson_geometry", {})
        params.update({"geojson_geometry": self.__geojson_geometry_to_feature(geojson_geometry)})
        with EnvContextManager(
            AWS_ACCESS_KEY_ID = params.get("aws_access_key_id",""),
            AWS_SECRET_ACCESS_KEY = params.get("aws_secret_access_key",""),
            AWS_NO_SIGN_REQUESTS = params.get("aws_no_sign_requests","NO"),
            AWS_REQUEST_PAYER = params.get("aws_request_payer","provider"),
            AWS_REGION = params.get("aws_region_name","")
        ):
            return self.stac_reader.render_mosaic_from_stac(params)
