from rasterio import warp
from rio_tiler.io import STACReader
from rio_tiler.mosaic import mosaic_reader
import io
import zipfile
import json
import os

class ReadSTAC:
    def __init__(self):
        self.default_crs = "EPSG:4326"
        self.formats = {"PNG":"PGW", "JPEG":"JGW"}

    @staticmethod
    def __tiler( item, *args, **kwargs):
        with STACReader(None, item=item) as stac:
            return stac.feature(*args,**kwargs)

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

    @staticmethod
    def __set_env_vars_read_s3(params):
        os.environ["AWS_ACCESS_KEY_ID"] = params.get("aws_access_key_id","")
        os.environ["AWS_SECRET_ACCESS_KEY"] = params.get("aws_secret_access_key","")
        os.environ["AWS_NO_SIGN_REQUESTS"] = params.get("aws_no_sign_requests","NO")
        os.environ["AWS_REQUEST_PAYER"] = params.get("aws_request_payer","provider")
        os.environ["AWS_REGION"] = params.get("aws_region_name","")

    @staticmethod
    def __unset_env_vars_read_s3():
        os.environ["AWS_ACCESS_KEY_ID"] = ""
        os.environ["AWS_SECRET_ACCESS_KEY"] = ""
        os.environ["AWS_NO_SIGN_REQUESTS"] = "NO"
        os.environ["AWS_REQUEST_PAYER"] = "provider"
        os.environ["AWS_REGION"] = ""


    def render_mosaic_from_stac(self, params):
        args = (params.get("geojson_geometry"), )
        kwargs = {
            "assets":  params.get("assets"),
            "max_size": params.get("max_size"),
            "nodata": params.get("nodata")
        }
        if params.get("image_format") not in self.formats:
            raise ValueError("Format not accepted")

        self.__set_env_vars_read_s3(params)
        image_data, assets_used = mosaic_reader(params.get("stac_list"), self.__tiler, *args, **kwargs)
        self.__unset_env_vars_read_s3()
        image = image_data.post_process(
            in_range=((params.get("min_value"), params.get("max_value")),),
            color_formula=params.get("color_formula"),
        )
        image = image.render(img_format=params.get("image_format"))
        image_bounds = self.__get_image_bounds(image_data)

        world_file = self.__get_world_file_content(image_bounds, image_data)
        if params.get("zip_file"):
            zip_file = self.__create_zip_geoimage(
                image,
                world_file,
                params.get("image_format"),
                params.get("geojson_geometry"),
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