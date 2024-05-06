import io
from PIL import Image
import pytest
import json
import numpy as np
from model.read_stac import ReadSTAC
import zipfile
import os

os.environ["GDAL_CACHEMAX"] = "200"
os.environ["GDAL_DISABLE_READDIR_ON_OPEN"] = "EMPTY_DIR"
os.environ["GDAL_HTTP_MULTIPLEX"] = "YES"
os.environ["GDAL_HTTP_MERGE_CONSECUTIVE_RANGES"] = "YES"
os.environ["GDAL_BAND_BLOCK_CACHE"] = "HASHSET"
os.environ["GDAL_HTTP_MAX_RETRY"] = "4"
os.environ["GDAL_HTTP_RETRY_DELAY"] = "0.42"
os.environ["GDAL_HTTP_VERSION"] = "2"
os.environ["CPL_VSIL_CURL_ALLOWED_EXTENSIONS"] = ".tif,.TIF,.tiff"
os.environ["CPL_VSIL_CURL_CACHE_SIZE"] = "200000000"
os.environ["VSI_CACHE"] = "TRUE"
os.environ["VSI_CACHE_SIZE"] = "5000000"
os.environ["PROJ_NETWORK"] = "OFF"

@pytest.fixture
def stac_item():
    with open("tests/data/stac_item.json") as test_data:
        return json.load(test_data)

@pytest.fixture
def feature_geojson():
    with open("tests/data/polygon_feature.geojson") as test_data:
        polygon_geojson = json.load(test_data)
    return {
            "type": "Feature",
            "properties": {},
            "geometry": polygon_geojson
        }

@pytest.fixture
def sample_image():
    with io.BytesIO() as buffer:
        # Write array to buffer
        image_data = Image.fromarray(np.zeros(100).astype(np.uint8))
        image_data.save(buffer, format="PNG")
        buffer.seek(0)
        return buffer.getvalue()

@pytest.fixture
def sample_image_array():
    return np.zeros(100)

@pytest.fixture
def sample_image_jpeg():
    with io.BytesIO() as buffer:
        # Write array to buffer
        image_data = Image.fromarray(np.zeros(100).astype(np.uint8))
        image_data.save(buffer, format="JPEG")
        buffer.seek(0)
        return buffer.getvalue()

@pytest.fixture
def sample_image_zip():
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
        # Save the PNG image to the zip file
        image_bytes_io = io.BytesIO()
        image_data = Image.fromarray(np.zeros(100).astype(np.uint8))
        image_data.save(image_bytes_io, format="PNG")
        image_bytes_io.seek(0)
        zip_file.writestr("image.png", image_bytes_io.getvalue())
        return zip_buffer.getvalue()

def test_init_read_stac():
    stac_reader = ReadSTAC()
    assert isinstance(stac_reader, ReadSTAC)

def test_render_mosaic(stac_item, feature_geojson, sample_image):
    image_format = "PNG"
    stac_list=[stac_item for i in range(2)]
    stac_reader = ReadSTAC()
    params = {
            "feature_geojson": feature_geojson,
            "stac_list": stac_list,
            "image_format": image_format,
            "assets":("red", "green", "blue"),
            "min_value": 0,
            "max_value": 4000,
            "max_size": 52
    }
    image_data = stac_reader.render_mosaic_from_stac(params)
    assert isinstance(image_data["image"], type(sample_image))
    assert isinstance(image_data["bounds"], list)
    assert isinstance(image_data["projection_file"], str)

def test_render_mosaic_jpeg(stac_item, feature_geojson, sample_image_jpeg):
    image_format = "JPEG"
    stac_list=[stac_item for i in range(2)]
    stac_reader = ReadSTAC()
    params = {
            "feature_geojson": feature_geojson,
            "stac_list": stac_list,
            "image_format": image_format,
            "assets":("red", "green", "blue"),
            "min_value": 0,
            "max_value": 4000,
            "max_size": 52
    }
    image_data = stac_reader.render_mosaic_from_stac(params)
    assert isinstance(image_data["image"], type(sample_image_jpeg))
    assert isinstance(image_data["bounds"], list)
    assert isinstance(image_data["projection_file"], str)

def test_render_mosaic_format_error(stac_item, feature_geojson):
    image_format = "GNP"
    stac_list=[stac_item for i in range(2)]
    stac_reader = ReadSTAC()
    params = {
            "feature_geojson": feature_geojson,
            "stac_list": stac_list,
            "image_format": image_format,
    }
    with pytest.raises(ValueError):
        stac_reader.render_mosaic_from_stac(params)

def test_render_mosaic_zip(stac_item, feature_geojson, sample_image_zip):
    image_format = "PNG"
    stac_list=[stac_item for i in range(2)]
    stac_reader = ReadSTAC()
    params = {
            "feature_geojson": feature_geojson,
            "stac_list": stac_list,
            "image_format": image_format,
            "zip_file": True,
            "assets":("red", "green", "blue"),
            "min_value": 0,
            "max_value": 4000,
            "max_size": 52
    }
    image_data = stac_reader.render_mosaic_from_stac(params)
    assert isinstance(image_data["zip_file"], type(sample_image_zip))

def test_render_mosaic_image_array(stac_item, feature_geojson, sample_image_array):
    image_format = "PNG"
    stac_list=[stac_item for i in range(2)]
    stac_reader = ReadSTAC()
    params = {
            "feature_geojson": feature_geojson,
            "stac_list": stac_list,
            "image_format": image_format,
            "assets":("red", "green", "blue"),
            "min_value": 0,
            "max_value": 4000,
            "max_size": 52,
            "image_as_array": True
    }
    image_data = stac_reader.render_mosaic_from_stac(params)
    assert isinstance(image_data["image"], type(sample_image_array))
    assert isinstance(image_data["bounds"], list)
    assert isinstance(image_data["projection_file"], str)

def test_render_mosaic_rgb_expression(stac_item, feature_geojson, sample_image_array):
    image_format = "PNG"
    stac_list=[stac_item for i in range(2)]
    stac_reader = ReadSTAC()
    params = {
            "feature_geojson": feature_geojson,
            "stac_list": stac_list,
            "image_format": image_format,
            "RGB-expression":{"assets": ("blue", "red", "green",), "expression": "blue,red,green-blue"},
            "min_value": 0,
            "max_value": 4000,
            "max_size": 52,
            "image_as_array": True
    }
    image_data = stac_reader.render_mosaic_from_stac(params)
    assert isinstance(image_data["image"], type(sample_image_array))
    assert isinstance(image_data["bounds"], list)
    assert isinstance(image_data["projection_file"], str)


def test_render_mosaic_enhance(stac_item, feature_geojson, sample_image_array):
    image_format = "PNG"
    stac_list=[stac_item for i in range(2)]
    stac_reader = ReadSTAC()
    params = {
            "feature_geojson": feature_geojson,
            "stac_list": stac_list,
            "image_format": image_format,
            "assets":("red", "green", "blue"),
            "compute_min_max": True,
            "max_size": 52,
            "image_as_array": True,
            "enhance_image": True
    }
    image_data = stac_reader.render_mosaic_from_stac(params)
    assert isinstance(image_data["image"], type(sample_image_array))
    assert isinstance(image_data["bounds"], list)
    assert isinstance(image_data["projection_file"], str)

def test_render_mosaic_enhance_passes(stac_item, feature_geojson, sample_image_array):
    image_format = "PNG"
    stac_list=[stac_item for i in range(2)]
    stac_reader = ReadSTAC()
    params = {
            "feature_geojson": feature_geojson,
            "stac_list": stac_list,
            "image_format": image_format,
            "assets":("red", "green", "blue"),
            "compute_min_max": True,
            "max_size": 52,
            "image_as_array": True,
            "enhance_image": True,
            "enhance_passes": 2
    }
    image_data = stac_reader.render_mosaic_from_stac(params)
    assert isinstance(image_data["image"], type(sample_image_array))
    assert isinstance(image_data["bounds"], list)
    assert isinstance(image_data["projection_file"], str)

def test_render_mosaic_enhance_passes_none(stac_item, feature_geojson, sample_image_array):
    image_format = "PNG"
    stac_list=[stac_item for i in range(2)]
    stac_reader = ReadSTAC()
    params = {
            "feature_geojson": feature_geojson,
            "stac_list": stac_list,
            "image_format": image_format,
            "assets":("red", "green", "blue"),
            "compute_min_max": True,
            "max_size": 52,
            "image_as_array": True,
            "enhance_image": True,
            "enhance_passes": 0
    }
    image_data = stac_reader.render_mosaic_from_stac(params)
    assert isinstance(image_data["image"], type(sample_image_array))
    assert isinstance(image_data["bounds"], list)
    assert isinstance(image_data["projection_file"], str)

def test_render_mosaic_image_expression(stac_item, feature_geojson, sample_image_array):
    image_format = "PNG"
    stac_list=[stac_item for i in range(2)]
    stac_reader = ReadSTAC()
    params = {
            "feature_geojson": feature_geojson,
            "stac_list": stac_list,
            "image_format": image_format,
            "expression":"red-green",
            "min_value": 0,
            "max_value": 4000,
            "max_size": 52,
            "image_as_array": True
    }
    image_data = stac_reader.render_mosaic_from_stac(params)
    assert isinstance(image_data["image"], type(sample_image_array))
    assert isinstance(image_data["bounds"], list)
    assert isinstance(image_data["projection_file"], str)

def test_render_mosaic_image_expression_minmax(stac_item, feature_geojson, sample_image_array):
    image_format = "PNG"
    stac_list=[stac_item for i in range(2)]
    stac_reader = ReadSTAC()
    params = {
            "feature_geojson": feature_geojson,
            "stac_list": stac_list,
            "image_format": image_format,
            "expression":"red-green",
            "compute_min_max": True,
            "max_size": 52,
            "image_as_array": True
    }
    image_data = stac_reader.render_mosaic_from_stac(params)
    assert isinstance(image_data["image"], type(sample_image_array))
    assert isinstance(image_data["bounds"], list)
    assert isinstance(image_data["projection_file"], str)

def test_render_mosaic_compute_minmax(stac_item, feature_geojson, sample_image):
    image_format = "PNG"
    stac_list=[stac_item for i in range(2)]
    stac_reader = ReadSTAC()
    params = {
            "feature_geojson": feature_geojson,
            "stac_list": stac_list,
            "image_format": image_format,
            "assets":("red", "green", "blue"),
            "compute_min_max": True,
            "max_size": 52
    }
    image_data = stac_reader.render_mosaic_from_stac(params)
    assert isinstance(image_data["image"], type(sample_image))
    assert isinstance(image_data["bounds"], list)
    assert isinstance(image_data["projection_file"], str)

def test_render_mosaic_rgb_expression_minmax(stac_item, feature_geojson, sample_image_array):
    image_format = "PNG"
    stac_list=[stac_item for i in range(2)]
    stac_reader = ReadSTAC()
    params = {
            "feature_geojson": feature_geojson,
            "stac_list": stac_list,
            "image_format": image_format,
            "RGB-expression":{"assets": ("blue", "red", "green",), "expression": "blue,red,green-blue"},
            "compute_min_max": True,
            "max_size": 52,
            "image_as_array": True
    }
    image_data = stac_reader.render_mosaic_from_stac(params)
    assert isinstance(image_data["image"], type(sample_image_array))
    assert isinstance(image_data["bounds"], list)
    assert isinstance(image_data["projection_file"], str)

def test_render_mosaic_zip_min_max(stac_item, feature_geojson, sample_image_zip):
    image_format = "PNG"
    stac_list=[stac_item for i in range(2)]
    stac_reader = ReadSTAC()
    params = {
            "feature_geojson": feature_geojson,
            "stac_list": stac_list,
            "image_format": image_format,
            "zip_file": True,
            "assets":("red", "green", "blue"),
            "compute_min_max": True,
            "max_size": 52
    }
    image_data = stac_reader.render_mosaic_from_stac(params)
    assert isinstance(image_data["zip_file"], type(sample_image_zip))


def test_render_mosaic_image_array_minmax(stac_item, feature_geojson, sample_image_array):
    image_format = "PNG"
    stac_list=[stac_item for i in range(2)]
    stac_reader = ReadSTAC()
    params = {
            "feature_geojson": feature_geojson,
            "stac_list": stac_list,
            "image_format": image_format,
            "assets":("red", "green", "blue"),
            "compute_min_max": True,
            "max_size": 52,
            "image_as_array": True
    }
    image_data = stac_reader.render_mosaic_from_stac(params)
    assert isinstance(image_data["image"], type(sample_image_array))
    assert isinstance(image_data["bounds"], list)
    assert isinstance(image_data["projection_file"], str)
