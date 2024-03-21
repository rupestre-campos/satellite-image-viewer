from rio_tiler.io import STACReader
from rasterio import warp
import numpy as np

class ReadSTAC:
    def __init__(self, stac_item, geojson_geometry):
        self.default_crs = "EPSG:4326"
        self.assets = ("red", "green", "blue",)
        self.stac_item = stac_item
        self.geojson_geometry = geojson_geometry

    @staticmethod
    def __brighten(band):
        alpha=0.13
        beta=0
        return np.clip(alpha*band+beta, 0,255)

    @staticmethod
    def __normalize(band):
        band_min, band_max = (band.min(), band.max())
        return ((band-band_min)/((band_max - band_min)))

    @staticmethod
    def __gammacorr(band):
        gamma=2
        return np.power(band, 1/gamma)

    def __get_image_bounds(self, image):
        left, bottom, right, top = [i for i in image.bounds]
        bounds_4326 = warp.transform_bounds(
            src_crs=image.crs,
            dst_crs=self.default_crs,
            left=left,
            bottom=bottom,
            right=right,
            top=top
        )

        return [[bounds_4326[1], bounds_4326[0]], [bounds_4326[3], bounds_4326[2]]]

    def render_image_from_stac(self):
        with STACReader(None, item=self.stac_item) as stac:
            image = stac.feature(
                self.geojson_geometry,
                assets=self.assets,
            )

        image_bounds = self.__get_image_bounds(image)
        image.rescale(in_range=((0, 4000),))

        image = image.data_as_image()
        image = self.__brighten(image)
        image = self.__normalize(image)
        image = self.__gammacorr(image)
        return {
            "image": image.data,
            "bounds": image_bounds,
            "name": self.stac_item["id"]
        }
