import pytest
import json
import numpy as np
from controller.image_renderer import ImageRenderer
from app_config import AppConfig

app_config_data = AppConfig()

@pytest.fixture
def stac_item():
    with open("tests/data/stac_item.json") as test_data:
        return json.load(test_data)

@pytest.fixture
def feature_geojson():
    with open("tests/data/polygon_feature.geojson") as test_data:
        return json.load(test_data)

@pytest.fixture
def sample_image():
    return np.zeros(50)

def test_init_read_stac(stac_item, feature_geojson):
    image_renderer = ImageRenderer(stac_item, feature_geojson)
    assert isinstance(image_renderer, ImageRenderer)

def test_render_image(mocker, stac_item, feature_geojson, sample_image):
    mocker.patch(
        "model.read_stac.ReadSTAC.render_image_from_stac",
        return_value={"image":sample_image, "bounds":[[0,0],[100,100]]}
    )
    image_renderer = ImageRenderer(stac_item, feature_geojson)

    image_data = image_renderer.render_image_from_stac()
    assert isinstance(image_data["image"], type(sample_image))
    assert isinstance(image_data["bounds"], list)