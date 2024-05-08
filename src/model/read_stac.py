import io
import zipfile
import json
from PIL import Image
import numpy as np
from rasterio import warp
from rasterio.transform import Affine
from rio_tiler.io import STACReader
from rio_tiler.models import ImageData
from rio_tiler.mosaic import mosaic_reader
from rio_tiler.colormap import cmap
from shapely.affinity import affine_transform
from shapely.geometry import LineString, MultiLineString, Point, mapping, shape
import numexpr as ne
from ISR.models import RDN
from skimage.measure import find_contours
from scipy.ndimage import gaussian_filter1d
from scipy.ndimage import maximum_filter


rdn = RDN(weights='psnr-small')

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

    @staticmethod
    def __array_to_png_string(image_array, image_format):
        # Convert the array to an image
        image = Image.fromarray(image_array)

        # Save the image to a bytes buffer
        with io.BytesIO() as buffer:
            image.save(buffer, format=image_format)
            png_string = buffer.getvalue()

        return png_string

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
        image = rdn.predict(image[:,:,:3], by_patch_of_size=50)

        alpha_channel_resized = self.__resize_alpha(alpha_channel, image)

        image = np.dstack((image, alpha_channel_resized))
        return self.__array_to_png_string(image, params.get("image_format", "PNG"))

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

    def __get_transform(self, transformed_bounds, width, height):
        min_y, min_x = transformed_bounds[0]
        max_y, max_x = transformed_bounds[1]

        pixel_size_x = round((max_x - min_x) / width, self.float_precision)
        pixel_size_y = round((max_y - min_y) / height, self.float_precision)

        transform = Affine(pixel_size_x, 0.0, min_x,
                           0.0, -pixel_size_y, max_y)
        return transform

    @staticmethod
    def __create_discrete_image(image, value_gap):
        discrete_image = (np.floor((image + value_gap + 1) / value_gap) * value_gap) - value_gap
        return discrete_image

    @staticmethod
    def __contours_from_image(image, contour_value, transform, min_vertices, sigma):
        features = []
        for contour in find_contours(image, contour_value):
            if contour.shape[0] < min_vertices:
                continue
            smoothed_coords = np.column_stack((
                gaussian_filter1d(contour[:, 0], sigma=sigma),
                gaussian_filter1d(contour[:, 1], sigma=sigma)
            ))
            if np.allclose(contour[0],contour[-1]):
                smoothed_coords = np.vstack((smoothed_coords, smoothed_coords[0]))
            features.append(LineString(smoothed_coords[:,[1,0]]))
        return affine_transform(MultiLineString(features), transform.to_shapely())

    def __get_contours(self, feature_geojson, image_data, gap, transform, min_vertices, sigma):
        quantized_image = self.__create_discrete_image(image_data.data, gap)
        feature_geometry = shape(feature_geojson['geometry'])
        features = []
        for pixel_value in np.unique(quantized_image):
            geom = self.__contours_from_image(
                quantized_image[0], pixel_value, transform, min_vertices, sigma)
            intersection = geom.intersection(feature_geometry)
            if intersection:
                feature = {
                    "type": "Feature",
                    "geometry": mapping(intersection),
                    "properties": {"pixel_value": round(float(pixel_value),self.float_precision) }
                }
                features.append(feature)

        neighborhood_size = (50, 50)
        local_max = maximum_filter(image_data.data[0], footprint=np.ones(neighborhood_size))
        local_max_points = np.argwhere(image_data.data[0] == local_max)
        features_point = []
        for point in local_max_points:
            pixel_value = image_data.data[0, point[0], point[1]]
            if pixel_value==0:
                continue
            geom = affine_transform(Point(point[1], point[0]), transform.to_shapely())
            intersection = geom.intersection(feature_geometry)
            if intersection:
                point_feature = {
                    "type": "Feature",
                    "geometry":  mapping(intersection),
                    "properties": {"pixel_value": round(float(pixel_value),self.float_precision)}
                }
                features_point.append(point_feature)

        features_point = sorted(
            features_point, key=lambda x: x.get("properties",{}).get("pixel_value"), reverse=True)
        features_point = features_point[:5]
        features += features_point
        feat_collection = {
            "type": "FeatureCollection",
            "features": features
        }
        return feat_collection

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
        transform = self.__get_transform(image_bounds, image_data.width, image_data.height)

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

        image = self.__post_process_image(image_data, params)
        image = self.__render_image(image, params)

        if params.get("enhance_image"):
            passes = params.get("enhance_passes", 1)
            for step in range(passes):
                image = self.__enhance_image(image, params)

        world_file = self.__get_world_file_content(image_bounds, image)
        contours = {}
        if params.get("create_contour"):
            min_vertices = params.get("min_vertices", 7)
            sigma = params.get("sigma", 0.8)
            gap = params.get("gap", 10)

            contours = self.__get_contours(
                feature_geojson, image_data, gap, transform, min_vertices, sigma)

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