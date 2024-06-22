import io
import zipfile
import json
from PIL import Image
import numpy as np
from rasterio import warp
from rio_tiler.io import STACReader
from rio_tiler.models import ImageData
from rio_tiler.mosaic import mosaic_reader
from rio_tiler.colormap import cmap
import numexpr as ne
from ISR.models import RDN
from osgeo import gdal, osr
import subprocess
import os
import tempfile

rdn = RDN(weights='psnr-small')

class ReadSTAC:
    def __init__(self, rdn_block_size=256):
        self.default_crs = "EPSG:4326"
        self.formats = {"PNG":"PGW", "JPEG":"JGW"}
        self.colormaps = cmap.list()
        self.float_precision = 5
        self.rdn_block_size = rdn_block_size

    @staticmethod
    def __tiler(item, *args, **kwargs):
        with STACReader(None, item=item) as stac:
            return stac.feature(*args, **kwargs)

    @staticmethod
    def __image_as_array(image):
        image = io.BytesIO(image)
        image = Image.open(image)
        return np.asarray(image)

    @staticmethod
    def __array_to_img_bytes(image_array, image_format):
        image = Image.fromarray(image_array)

        with io.BytesIO() as buffer:
            image.save(buffer, format=image_format)
            img_bytes = buffer.getvalue()

        return img_bytes

    @staticmethod
    def __get_view_params(params):
        if "expression" in params:
            return "expression", params.get("expression")
        if "RGB-expression" in params:
            return "assets", params["RGB-expression"].get("assets")
        return "assets", params.get("assets")

    @staticmethod
    def __process_rgb_expression(image_data, params):
        ctx = {}
        for bdx, band in enumerate(params["RGB-expression"].get("assets")):
            ctx[band] = image_data.data[bdx]
        expression = params["RGB-expression"].get("expression").split(",")
        mask = np.invert(image_data.mask)
        masks = (mask,mask,mask)
        data = np.ma.MaskedArray(
            np.array(
                [np.nan_to_num(ne.evaluate(band.strip(), local_dict=ctx)) for band in expression]
            ),
            mask=masks
        )
        return ImageData(data)

    @staticmethod
    def __resize_alpha(alpha_channel, image):
        return np.array(
            Image.fromarray(alpha_channel).resize((image.shape[1], image.shape[0]), Image.NEAREST))

    def __enhance_image(self, image, params):
        image = self.__image_as_array(image)
        alpha_channel = image[:, :, 3]
        image = rdn.predict(image[:,:,:3], by_patch_of_size=self.rdn_block_size)

        alpha_channel_resized = self.__resize_alpha(alpha_channel, image)

        image = np.dstack((image, alpha_channel_resized))
        return self.__array_to_img_bytes(image, params.get("image_format", "PNG"))

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

    def __get_world_file_content(self, image_bounds, image):
        image = self.__image_as_array(image)
        return (
            f"{abs(image_bounds[0][1] - image_bounds[1][1]) / image.shape[1]}\n"
            f"0.0\n"
            f"0.0\n"
            f"{-abs(image_bounds[0][0] - image_bounds[1][0]) / image.shape[0]}\n"
            f"{image_bounds[0][1]}\n"
            f"{image_bounds[1][0]}\n"
        )

    def __create_zip_geoimage(self, image, world_file, image_format, geometry, assets_used, contours):
        extension = image_format.lower()
        extension_world_file = self.formats[image_format].lower()
        zip_buffer = io.BytesIO()
        image_metadata = {"type":"FeatureCollection","features":assets_used}
        with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
            zip_file.writestr(f"image.{extension}", image)
            zip_file.writestr(f"image.{extension_world_file}", world_file.encode())
            zip_file.writestr(f"polygon.geojson", json.dumps(geometry).encode())
            zip_file.writestr(f"image_metadata.geojson", json.dumps(image_metadata).encode())
            if contours:
                zip_file.writestr(f"contours.geojson", json.dumps(contours).encode())

        return zip_buffer.getvalue()

    def __post_process_image(self, image_data, params):
        min_value = params.get("min_value")
        max_value = params.get("max_value")

        if params.get("assets"):
            return image_data.post_process(
                in_range=((min_value, max_value),),
                color_formula=params.get("color_formula"),
            )
        if params.get("RGB-expression"):
            return image_data.post_process(
                in_range=((min_value, max_value),),
                color_formula=params.get("color_formula"),
            )

        return image_data.post_process(
            in_range=((
                min_value,
                max_value,
            ),),
        )

    def __render_image(self, image, params):
        if params.get("assets"):
            return image.render(img_format=params.get("image_format"))
        if params.get("RGB-expression"):
            return image.render(img_format=params.get("image_format"))

        input_colormap = params.get("colormap", "viridis")
        colormap = cmap.get(input_colormap)
        return image.render(
            img_format=params.get("image_format"),
            colormap=colormap
        )

    @staticmethod
    def __colorize_hillshade(hillshade, mask, colormap="gray"):
        hillshade = hillshade.astype(np.uint8)

        color_map = cmap.get(colormap)
        colorized_hillshade = np.zeros((hillshade.shape[0], hillshade.shape[1], 4), dtype=np.uint8)

        for value, color in color_map.items():
            mask_value = hillshade == value
            colorized_hillshade[mask_value, :3] = color[:3]

        colorized_hillshade[:, :, 3] = mask
        return colorized_hillshade

    @staticmethod
    def __create_hillshade(arr, azimuth=30, altitude=30, exaggeration=100):
        # azimuth <= 360 and altitude <90 to this to work
        x, y = np.gradient(arr)

        azimuth = 360.0 - azimuth
        azimuthrad = azimuth * np.pi / 180.0
        altituderad = altitude * np.pi / 180.0

        slope = np.pi / 2.0 - np.arctan(np.sqrt(x * x + y * y))
        aspect = np.arctan2(-x, y)

        shaded = np.sin(altituderad) * np.sin(slope) + np.cos(
            altituderad
        ) * np.cos(slope) * np.cos((azimuthrad - np.pi / 2.0) - aspect)

        return 255 * (shaded + 1) / 2

    @staticmethod
    def __get_contours(image_data, interval=10):
        image_array = image_data.data.squeeze()
        if image_data.mask is not None:
            image_array[image_data.mask == 0] = -12000  # Set nodata value to -12000

        temp_input_tif = tempfile.NamedTemporaryFile(suffix=".tif").name
        driver = gdal.GetDriverByName("GTiff")
        output_dataset = driver.Create(temp_input_tif, image_array.shape[1], image_array.shape[0], 1, gdal.GDT_Float32)
        output_dataset.GetRasterBand(1).WriteArray(image_array)
        output_dataset.GetRasterBand(1).SetNoDataValue(-32000)

        srs = osr.SpatialReference()
        srs.ImportFromEPSG(4326)  # Set the desired EPSG code
        output_dataset.SetProjection(srs.ExportToWkt())

        if image_data.bounds:
            geotransform = [
                image_data.bounds[0],  # xmin
                (image_data.bounds[2] - image_data.bounds[0]) / image_array.shape[1],
                0,
                image_data.bounds[3],  # ymax
                0,
                -(image_data.bounds[3] - image_data.bounds[1]) / image_array.shape[0]
            ]
            output_dataset.SetGeoTransform(geotransform)

        # Close and clean the temporary GeoTIFF file
        output_dataset = None

        # Create a temporary GeoJSON file
        temp_output_geojson = tempfile.NamedTemporaryFile(suffix=".geojson").name

        try:
            # Run gdal_contour command
            command = [
                "gdal_contour",
                "-a",
                "pixel_value",  # Attribute name for contour lines
                "-i",
                str(interval),  # Contour interval
                "-snodata",
                "-12000",
                "-f",
                "GeoJSON",  # Output format
                temp_input_tif,
                temp_output_geojson,
            ]
            subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            # Read the generated GeoJSON file
            with open(temp_output_geojson, 'r') as f:
                geojson_data = json.load(f)

        except subprocess.CalledProcessError as e:
            print(f"Error running gdal_contour: {e}")
            stdout = e.stdout.decode('utf-8')
            stderr = e.stderr.decode('utf-8')
            print(f"gdal_contour stdout:\n{stdout}")
            print(f"gdal_contour stderr:\n{stderr}")
            raise  # Re-raise the exception for handling at higher level

        finally:
            # Clean up: Delete temporary files
            if os.path.exists(temp_input_tif):
                os.remove(temp_input_tif)
            if os.path.exists(temp_output_geojson):
                os.remove(temp_output_geojson)

        return geojson_data

    @staticmethod
    def merge_altitude_and_hillshade(image_altitude_bytes, image_hillshade_bytes):
        image1 = Image.open(io.BytesIO(image_altitude_bytes))
        image2 = Image.open(io.BytesIO(image_hillshade_bytes))
        composite = Image.blend(image1, image2, alpha=0.5)  # Adjust alpha as needed

        buffer = io.BytesIO()
        composite.save(buffer, format="PNG")
        composite_bytes = buffer.getvalue()

        return composite_bytes

    def render_mosaic_from_stac(self, params):
        if params.get("image_format") not in self.formats:
            raise ValueError("Format not accepted")
        feature_geojson = params.get("feature_geojson")
        args = (feature_geojson, )
        view_type, view_params  = self.__get_view_params(params)
        kwargs = {
            view_type:  view_params,
            "max_size": params.get("max_size"),
            "nodata": params.get("nodata"),
            "asset_as_band": True
        }
        image_data, assets_used = mosaic_reader(
            params.get("stac_list"), self.__tiler, *args, **kwargs)
        image_bounds = self.__get_image_bounds(image_data)

        if params.get("RGB-expression"):
            image_data = self.__process_rgb_expression(image_data, params)
        min_value = params.get("min_value")
        max_value = params.get("max_value")
        if params.get("compute_min_max"):
            min_value = round(
                image_data.data[image_data.data!=params.get("nodata")].min(), self.float_precision)
            max_value = round(
                image_data.data[image_data.data!=params.get("nodata")].max(), self.float_precision)
            params.update({"min_value": min_value, "max_value": max_value})

        if params.get("create_contour"):
            image = self.__post_process_image(image_data, params)
            params["colormap"] = "terrain"
            image_altitude = self.__render_image(image, params)
            image = self.__create_hillshade(image_data.data.squeeze())
            image_hillshade = self.__array_to_img_bytes(
                self.__colorize_hillshade(image, image_data.mask, "gray"),
                params.get("image_format","PNG")
            )
            image = self.merge_altitude_and_hillshade(image_altitude, image_hillshade)

        if not params.get("create_contour"):
            image = self.__post_process_image(image_data, params)
            image = self.__render_image(image, params)

        if params.get("enhance_image"):
            passes = params.get("enhance_passes", 1)
            for step in range(passes):
                image = self.__enhance_image(image, params)

        world_file = self.__get_world_file_content(image_bounds, image)
        contours = {}
        if params.get("create_contour"):
            gap = params.get("gap", 10)
            contours = self.__get_contours(
                image_data,
                gap
            )

        if params.get("zip_file"):
            zip_file = self.__create_zip_geoimage(
                image,
                world_file,
                params.get("image_format"),
                params.get("feature_geojson"),
                assets_used,
                contours
            )

        if params.get("image_as_array"):
            image = self.__image_as_array(image)

        if params.get("zip_file"):
            return {
                "image": image,
                "bounds": image_bounds,
                "zip_file": zip_file,
                "contours": contours,
                "min_value": params.get("min_value"),
                "max_value": params.get("max_value"),
                "name": ", ".join(sorted([item["id"] for item in assets_used]))
            }

        return {
            "image": image,
            "projection_file": world_file,
            "bounds": image_bounds,
            "assets_used": assets_used,
            "contours": contours,
            "min_value": params.get("min_value"),
            "max_value": params.get("max_value"),
            "name": ", ".join(sorted([item["id"] for item in assets_used]))
        }