import numpy as np
from rasterio import warp
from rio_tiler.io import STACReader
from rio_tiler.mosaic import mosaic_reader

class ReadSTAC:
    def __init__(
            self,
            stac_item={},
            stac_list=[],
            geojson_geometry={}
        ):
        self.default_crs = "EPSG:4326"
        self.assets = ("red", "green", "blue",)
        self.stac_item = stac_item
        self.stac_list = stac_list
        self.geojson_geometry = geojson_geometry
        self.min_value = 0
        self.max_value = 4000
        self.alpha = 0.13
        self.beta = 0
        self.gamma = 2

    @staticmethod
    def __normalize(image):
        image_min, image_max = (image.min(), image.max())
        return ((image-image_min)/((image_max - image_min)))

    @staticmethod
    def __tiler(item, *args, **kwargs):
        with STACReader(None, item=item) as stac:
            return stac.feature(*args,**kwargs)

    def __brighten(self, image):
        return np.clip(
            self.alpha*image+self.beta, 0, 255)

    def __gammacorr(self, image):
        return np.power(image, 1/self.gamma)

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

    def __apply_contrast(self, image):
        image = self.__brighten(image)
        image = self.__normalize(image)
        image = self.__gammacorr(image)
        return image

    def render_image_from_stac(self):
        args = (self.geojson_geometry,)
        kwargs = {'assets': self.assets}
        image_data = self.__tiler(self.stac_item, *args, **kwargs)
        image_data.rescale(in_range=((self.min_value, self.max_value),))
        image = image_data.data_as_image()
        image = self.__apply_contrast(image)
        image_bounds = self.__get_image_bounds(image_data)

        return {
            "image": image.data,
            "bounds": image_bounds,
            "name": self.stac_item["id"]
        }

    def render_mosaic_from_stac(self):
        args = (self.geojson_geometry, )
        kwargs = {'assets': self.assets}
        image_data, assets_used = mosaic_reader(self.stac_list, self.__tiler, *args, **kwargs)
        image_data.rescale(in_range=((self.min_value, self.max_value),))
        image = image_data.data_as_image()
        image = self.__apply_contrast(image)
        image_bounds = self.__get_image_bounds(image_data)

        return {
            "image": image.data,
            "bounds": image_bounds,
            "assets_used": assets_used
        }