import pytest
import json
from controller.point_bufferer import PointBufferer

@pytest.fixture
def feature_geojson():
    with open("tests/data/polygon_feature.geojson") as test_data:
        return json.load(test_data)

def test_init_point_bufferer():
    point_bufferer = PointBufferer()
    assert isinstance(point_bufferer, PointBufferer)

def test_search_address(mocker, feature_geojson):
    latitude = 10
    longitude = 100
    distance = 10
    mocker.patch(
        "model.buffer_point.BufferPoint.buffer",
        return_value=feature_geojson
    )
    point_bufferer = PointBufferer()

    result = point_bufferer.buffer(latitude, longitude, distance)
    assert isinstance(result, dict)
