import io
import zipfile
import json
from PIL import Image
import numpy as np
from rasterio import warp
from rio_tiler.io import STACReader
from rio_tiler.mosaic import mosaic_reader
from rio_tiler.colormap import cmap


class ReadSTAC:
    def __init__(self):
        self.default_crs = "EPSG:4326"
        self.formats = {"PNG":"PGW", "JPEG":"JGW"}
        self.colormaps = cmap.list()
        self.float_precision = 5

    @staticmethod
    def __tiler(item, *args, **kwargs):
        with STACReader(None, item=item) as stac:
            return stac.feature(*args, **kwargs)

    @staticmethod
    def __image_as_array(image):
        image = io.BytesIO(image)
        image = Image.open(image)
        return np.asarray(image)

    def __get_image_bounds(self, image):
        left, bottom, right, top = [round(i, self.float_precision) for i in image.bounds]
        bounds_4326 = warp.transform_bounds(
            src_crs=image.crs,
            dst_crs=self.default_crs,
            left=left,
            bottom=bottom,
            right=right,
            top=top
        )
        bounds_4326 = [round(i, self.float_precision) for i in bounds_4326]
        return [[bounds_4326[1], bounds_4326[0]], [bounds_4326[3], bounds_4326[2]]]

    def __get_world_file_content(self, image_bounds, image_data):
        return (
            f"{abs(image_bounds[0][1] - image_bounds[1][1]) / image_data.width}\n"
            f"0.0\n"
            f"0.0\n"
            f"{-abs(image_bounds[0][0] - image_bounds[1][0]) / image_data.height}\n"
            f"{image_bounds[0][1]}\n"
            f"{image_bounds[1][0]}\n"
        )

    def __create_zip_geoimage(self, image, world_file, image_format, geometry, assets_used):
        extension = image_format.lower()
        extension_world_file = self.formats[image_format].lower()
        zip_buffer = io.BytesIO()
        image_metadata = {"type":"FeatureCollection","features":assets_used}
        with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
            zip_file.writestr(f"image.{extension}", image)
            zip_file.writestr(f"image.{extension_world_file}", world_file.encode())
            zip_file.writestr(f"polygon.geojson", json.dumps(geometry).encode())
            zip_file.writestr(f"image_metadata.geojson", json.dumps(image_metadata).encode())

        return zip_buffer.getvalue()

    def __post_process_image(self, image_data, params):
        if params.get("assets"):
            return image_data.post_process(
                in_range=((params.get("min_value"), params.get("max_value")),),
                color_formula=params.get("color_formula"),
            )

        return image_data.post_process(
            in_range=((
                params.get("min_value",-1),
                params.get("max_value", 1),
            ),),
        )

    def __render_image(self, image, params):
        if params.get("assets"):
            return image.render(img_format=params.get("image_format"))

        colormap = cmap.get(params.get("colormap", "viridis"))
        return image.render(
            img_format=params.get("image_format"),
            colormap=colormap
        )

    def render_mosaic_from_stac(self, params):
        args = (params.get("feature_geojson"), )
        view_params = "assets" if params.get("assets") else "expression"
        kwargs = {
            view_params:  params.get(view_params),
            "max_size": params.get("max_size"),
            "nodata": params.get("nodata"),
            "asset_as_band": True
        }
        if params.get("image_format") not in self.formats:
            raise ValueError("Format not accepted")

        image_data, assets_used = mosaic_reader(
            params.get("stac_list"), self.__tiler, *args, **kwargs)

        image = self.__post_process_image(image_data, params)
        image = self.__render_image(image, params)
        image_bounds = self.__get_image_bounds(image_data)
        world_file = self.__get_world_file_content(image_bounds, image_data)

        if params.get("zip_file"):
            zip_file = self.__create_zip_geoimage(
                image,
                world_file,
                params.get("image_format"),
                params.get("feature_geojson"),
                assets_used
            )

        if params.get("image_as_array"):
            image = self.__image_as_array(image)

        if params.get("zip_file"):
            return {
                "image": image,
                "bounds": image_bounds,
                "zip_file": zip_file,
                "name": ", ".join(sorted([item["id"] for item in assets_used]))
            }

        return {
            "image": image,
            "projection_file": world_file,
            "bounds": image_bounds,
            "assets_used": assets_used,
            "name": ", ".join(sorted([item["id"] for item in assets_used]))
        }