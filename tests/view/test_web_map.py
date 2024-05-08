import pytest
import json
import numpy as np
from view.web_map import WebMap
from app_config import AppConfig

app_config_data = AppConfig()

@pytest.fixture
def tile_url():
    return app_config_data.google_basemap

@pytest.fixture
def web_map():
    return WebMap()

@pytest.fixture
def feature_geojson():
    with open("tests/data/polygon_feature.geojson") as test_data:
        return json.load(test_data)

@pytest.fixture
def feature_contours():
    with open("tests/data/contours.geojson") as test_data:
        return json.load(test_data)

@pytest.fixture
def sample_image():
    return np.zeros(50)

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
    draw_child = [item for item in map_children if item.startswith('draw')]
    assert len(draw_child) == 1

def test_web_map_fullscreen(web_map):
    web_map.add_fullscreen()
    map_children = list(web_map.web_map._children.keys())
    fullscreen_child = [item for item in map_children if item.startswith('fullscreen')]
    assert len(fullscreen_child) == 1

def test_web_map_mouse(web_map):
    web_map.add_mouse_location()
    map_children = list(web_map.web_map._children.keys())
    mouse_child = [item for item in map_children if item.startswith('mouse')]
    assert len(mouse_child) == 1

def test_render_web_map_empty(web_map):
    assert web_map.render_web_map() == {"geometry": None}

def test_render_web_map_drawn(mocker, web_map, feature_geojson):
    test_value = {"last_active_drawing":{"geometry":feature_geojson}}
    mocker.patch("view.web_map.WebMap._streamlit_render", return_value=test_value)
    assert web_map.render_web_map() == {"geometry":feature_geojson}

def test_add_polygon(web_map, feature_geojson):
    web_map.add_polygon(feature_geojson)
    assert isinstance(web_map, WebMap)

def test_add_image(web_map, sample_image):
    web_map.add_image(sample_image, [[0,0],[100,100]])
    assert isinstance(web_map, WebMap)

def test_add_layer_control(web_map):
    web_map.add_layer_control()
    map_children = list(web_map.web_map._children.keys())
    layer_control_child = [item for item in map_children if item.startswith('layer_control')]
    assert len(layer_control_child) == 1

def test_add_basemap(web_map, tile_url):
    web_map.add_base_map(tile_url, "google_basemap", "google")
    map_children = list(web_map.web_map._children.keys())
    basemap_child = [item for item in map_children if item.startswith('tile_layer')]
    assert len(basemap_child) == 1

def test_add_contour(web_map, feature_contours):
    web_map.add_contour(feature_contours)
    assert isinstance(web_map, WebMap)