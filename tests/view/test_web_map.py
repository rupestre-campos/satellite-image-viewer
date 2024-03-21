import pytest
import json
from view.web_map import WebMap

@pytest.fixture
def web_map():
    return WebMap()

@pytest.fixture
def feature_geojson():
    with open("tests/data/polygon_feature.geojson") as test_data:
        return json.load(test_data)

def test_instance_web_map(web_map):
    assert isinstance(web_map, WebMap)

def test_web_map():
    zoom_start = 5
    center_y = -21
    center_x = -45
    map_object = WebMap(center_y=center_y, center_x=center_x, zoom_start=zoom_start)
    assert map_object.web_map.location == [center_y, center_x]
    assert map_object.web_map.options["zoom"] == zoom_start

def test_web_map_draw(web_map):
    web_map.add_draw_support(export=False)
    map_children = list(web_map.web_map._children.keys())
    draw_children = [item for item in map_children if item.startswith('draw')]
    assert len(draw_children) == 1

def test_render_web_map_empty(web_map):
    assert web_map.render_web_map() == {"geometry": None}

def test_render_web_map_drawn(mocker, web_map):
    test_value = {"last_active_drawing":{"geometry":feature_geojson}}
    mocker.patch("view.web_map.WebMap._streamlit_render", return_value=test_value)
    assert web_map.render_web_map() == {"geometry":feature_geojson}