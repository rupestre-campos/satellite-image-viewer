import pytest
import json
import numpy as np
from model.read_stac import ReadSTAC

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
    return np.array(0)

def test_init_read_stac(feature_geojson):
    stac_reader = ReadSTAC()
    assert isinstance(stac_reader, ReadSTAC)

def test_render_image(stac_item, feature_geojson, sample_image):
    stac_reader = ReadSTAC(
        stac_item=stac_item,
        geojson_geometry=feature_geojson)
    image_data = stac_reader.render_image_from_stac()
    assert isinstance(image_data["image"], type(sample_image))
    assert isinstance(image_data["bounds"], list)

def test_render_mosaic(stac_item, feature_geojson, sample_image):
    stac_reader = ReadSTAC(
        stac_list=[stac_item for i in range(10)],
        geojson_geometry=feature_geojson)
    image_data = stac_reader.render_mosaic_from_stac()
    assert isinstance(image_data["image"], type(sample_image))
    assert isinstance(image_data["bounds"], list)