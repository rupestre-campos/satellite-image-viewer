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

        return self.stac_reader.render_mosaic_from_stac(params)
