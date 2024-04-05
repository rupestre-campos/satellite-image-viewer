import io
import json
import pytest
import numpy as np
from PIL import Image
from datetime import datetime
from datetime import timedelta
from controller.animation_creator import AnimationCreator
from controller.catalog_searcher import CatalogSearcher
from controller.image_renderer import ImageRenderer

@pytest.fixture
def stac_item():
    with open("tests/data/stac_item.json") as test_data:
        return json.load(test_data)

@pytest.fixture
def sample_image():
    with io.BytesIO() as buffer:
        # Write array to buffer
        image_data = Image.open("tests/data/image.png", formats=["PNG"])
        image_data.save(buffer, format="PNG")
        buffer.seek(0)
        return buffer.getvalue()

@pytest.fixture
def sample_image_gif(sample_image):
    image = io.BytesIO(sample_image)
    image = Image.open(image)
    image_list = [image for i in range(10)]
    with io.BytesIO() as buffer:
        # Write array to buffer
        image_list[0].save(
            fp=buffer,
            format="GIF",
            append_images=image_list[1:],
            save_all=True,
            duration=len(image_list),
            loop=0
        )
        buffer.seek(0)
        return buffer.getvalue()


@pytest.fixture
def feature_geojson():
    with open("tests/data/polygon_feature.geojson") as test_data:
        return json.load(test_data)

@pytest.fixture
def datestring():
    end_date = datetime.now()
    start_date = end_date - timedelta(days=10)
    return f"{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}"

def test_init_class(mocker):
    mocker.patch("model.search_stac.SearchSTAC.connect_client", return_value=None)
    catalog_searcher = CatalogSearcher(stac_url="test.ai")
    image_renderer = ImageRenderer()
    animation_creator = AnimationCreator(catalog_searcher, image_renderer)
    assert isinstance(animation_creator, AnimationCreator)

def test_create_gif(mocker, datestring, stac_item, sample_image, sample_image_gif, feature_geojson):
    mocker.patch("model.search_stac.SearchSTAC.connect_client", return_value=None)
    mocker.patch("model.search_stac.SearchSTAC.get_items", return_value=[stac_item])
    mocker.patch(
        "model.read_stac.ReadSTAC.render_mosaic_from_stac",
        return_value={"image":sample_image, "bounds":[[0,0],[100,100]]}
    )
    catalog_searcher = CatalogSearcher(stac_url="test.ai")
    image_renderer = ImageRenderer()
    animation_creator = AnimationCreator(catalog_searcher, image_renderer)
    params = {
        "feature_geojson": feature_geojson,
        "date_string": datestring,
        "period_time_break": 180,
        "time_per_image": 0.3,
        "image_search":{
            "max_cloud_cover": 100,
            "collection": "sentinel-2-l2a"},
        "image_render":{
            "assets":("red", "green", "blue"),
            "min_value": 0,
            "max_value": 4000,
            "max_size": 52,
        }
    }
    image_data = animation_creator.create_gif(params)
    assert isinstance(image_data["image"], type(sample_image_gif))
    assert isinstance(image_data["bounds"], list)

def test_create_gif_empty(mocker, datestring, stac_item, sample_image_gif, feature_geojson):
    mocker.patch("model.search_stac.SearchSTAC.connect_client", return_value=None)
    mocker.patch("model.search_stac.SearchSTAC.get_items", return_value=[])

    catalog_searcher = CatalogSearcher(stac_url="test.ai")
    image_renderer = ImageRenderer()
    animation_creator = AnimationCreator(catalog_searcher, image_renderer)
    params = {
        "feature_geojson": feature_geojson,
        "date_string": datestring,
        "image_search":{
            "max_cloud_cover": 100,
            "collection": "sentinel-2-l2a"},
        "image_render":{
            "assets":("red", "green", "blue"),
            "min_value": 0,
            "max_value": 4000,
            "max_size": 52,
        }
    }

    with pytest.raises(ValueError):
        image_data = animation_creator.create_gif(params)