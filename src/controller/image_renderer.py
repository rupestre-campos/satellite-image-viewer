from model.read_stac import ReadSTAC

class ImageRenderer:
    def __init__(self, stac_item={}, stac_list=[], geojson_geometry={}):
        self.default_crs = "EPSG:4326"
        self.assets = ("red", "green", "blue",)
        self.stac_item = stac_item
        self.stac_list = stac_list
        self.geojson_geometry = self.__geojson_geometry_to_feature(geojson_geometry)

    @staticmethod
    def __geojson_geometry_to_feature(geojson_geometry):
        return {
            "type": "Feature",
            "properties": {},
            "geometry": geojson_geometry
        }

    def render_image_from_stac(self):
        stac_reader = ReadSTAC(
            stac_item=self.stac_item,
            geojson_geometry=self.geojson_geometry)
        return stac_reader.render_image_from_stac()

    def render_mosaic_from_stac(self):
        stac_reader = ReadSTAC(
            stac_list=self.stac_list,
            geojson_geometry=self.geojson_geometry)
        return stac_reader.render_mosaic_from_stac()
