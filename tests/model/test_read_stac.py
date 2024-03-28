import io
from PIL import Image
import pytest
import json
import numpy as np
from model.read_stac import ReadSTAC
import zipfile

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

def test_init_read_stac(feature_geojson):
    stac_reader = ReadSTAC()
    assert isinstance(stac_reader, ReadSTAC)

def test_render_mosaic(stac_item, feature_geojson, sample_image):
    image_format = "PNG"
    stac_reader = ReadSTAC(
        stac_list=[stac_item for i in range(2)],
        geojson_geometry=feature_geojson)
    image_data = stac_reader.render_mosaic_from_stac(image_format=image_format)
    assert isinstance(image_data["image"], type(sample_image))
    assert isinstance(image_data["bounds"], list)
    assert isinstance(image_data["projection_file"], str)

def test_render_mosaic_jpeg(stac_item, feature_geojson, sample_image_jpeg):
    image_format = "JPEG"
    stac_reader = ReadSTAC(
        stac_list=[stac_item for i in range(2)],
        geojson_geometry=feature_geojson)
    image_data = stac_reader.render_mosaic_from_stac(image_format=image_format)
    assert isinstance(image_data["image"], type(sample_image_jpeg))
    assert isinstance(image_data["bounds"], list)
    assert isinstance(image_data["projection_file"], str)

def test_render_mosaic_format_error(stac_item, feature_geojson, sample_image):
    image_format = "GNP"
    stac_reader = ReadSTAC(
        stac_list=[stac_item for i in range(2)],
        geojson_geometry=feature_geojson)
    with pytest.raises(ValueError):
        stac_reader.render_mosaic_from_stac(image_format=image_format)

def test_render_mosaic_zip(stac_item, feature_geojson, sample_image_zip):
    image_format = "PNG"
    stac_reader = ReadSTAC(
        stac_list=[stac_item for i in range(2)],
        geojson_geometry=feature_geojson)
    image_data = stac_reader.render_mosaic_from_stac(image_format=image_format, zip_file=True)
    assert isinstance(image_data["zip_file"], type(sample_image_zip))
