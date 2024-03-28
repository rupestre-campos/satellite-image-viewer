from rasterio import warp
from rio_tiler.io import STACReader
from rio_tiler.mosaic import mosaic_reader
import io
import zipfile
import json

class ReadSTAC:
    def __init__(
            self,
            stac_item={},
            stac_list=[],
            geojson_geometry={},
            nodata=0,
            min_value=0,
            max_value=4000
        ):
        self.default_crs = "EPSG:4326"
        self.assets = ("red", "green", "blue",)
        self.formats = {"PNG":"PGW", "JPEG":"JGW"}
        self.stac_item = stac_item
        self.stac_list = stac_list
        self.geojson_geometry = geojson_geometry
        self.min_value = min_value
        self.max_value = max_value
        self.nodata = nodata
        self.color_formula = "sigmoidal RGB 6 0.1 gamma G 1.1 gamma B 1.2 saturation 1.2"

    @staticmethod
    def __tiler(item, *args, **kwargs):
        with STACReader(None, item=item) as stac:
            return stac.feature(*args,**kwargs)

    @staticmethod
    def __parse_image_format(image_format):
        if image_format=="JPEG":
            return "JPEG"
        return image_format

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

    def render_mosaic_from_stac(self, image_format="PNG", zip_file=False):
        args = (self.geojson_geometry, )
        kwargs = {"assets": self.assets, "max_size": None, "nodata":0}
        if image_format not in self.formats:
            raise ValueError("Format not accepted")
        image_data, assets_used = mosaic_reader(self.stac_list, self.__tiler, *args, **kwargs)

        image = image_data.post_process(
            in_range=((self.min_value, self.max_value),),
            color_formula=self.color_formula,
        )
        image = image.render(img_format=self.__parse_image_format(image_format))
        image_bounds = self.__get_image_bounds(image_data)

        world_file = self.__get_world_file_content(image_bounds, image_data)
        if zip_file:
            zip_file = self.__create_zip_geoimage(
                image,
                world_file,
                image_format,
                self.geojson_geometry,
                assets_used
            )
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