import pytest
import json
import zipfile
from PIL import Image
import io
import numpy as np
from controller.image_renderer import ImageRenderer
from app_config import AppConfig

app_config_data = AppConfig()

@pytest.fixture
def stac_item():
    with open("tests/data/stac_item.json") as test_data:
        return json.load(test_data)

@pytest.fixture
def stac_list():
    with open("tests/data/stac_item.json") as test_data:
        data = json.load(test_data)
    return [data for i in range(10)]

@pytest.fixture
def feature_geojson():
    with open("tests/data/polygon_feature.geojson") as test_data:
        return json.load(test_data)

@pytest.fixture
def sample_image():
    with io.BytesIO() as buffer:
        # Write array to buffer
        image_data = Image.fromarray(np.zeros(100).astype(np.uint8))
        image_data.save(buffer, format="PNG")
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

def test_init_read_stac(stac_item, feature_geojson):
    image_renderer = ImageRenderer(stac_item, feature_geojson)
    assert isinstance(image_renderer, ImageRenderer)

def test_render_mosaic(mocker, stac_list, feature_geojson, sample_image):
    mocker.patch(
        "model.read_stac.ReadSTAC.render_mosaic_from_stac",
        return_value={"image":sample_image, "bounds":[[0,0],[100,100]]}
    )
    image_renderer = ImageRenderer(stac_list=stac_list, geojson_geometry=feature_geojson)

    image_data = image_renderer.render_mosaic_from_stac()
    assert isinstance(image_data["image"], type(sample_image))
    assert isinstance(image_data["bounds"], list)


def test_render_mosaic(mocker, stac_list, feature_geojson, sample_image_zip):
    mocker.patch(
        "model.read_stac.ReadSTAC.render_mosaic_from_stac",
        return_value={"zip_file":sample_image_zip }
    )
    image_renderer = ImageRenderer(stac_list=stac_list, geojson_geometry=feature_geojson)

    image_data = image_renderer.render_mosaic_from_stac(zip_file=True)
    assert isinstance(image_data["zip_file"], type(sample_image_zip))
