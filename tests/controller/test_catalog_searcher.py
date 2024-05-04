import pytest
import json
from controller.catalog_searcher import CatalogSearcher

from datetime import datetime


@pytest.fixture
def stac_url():
    return "http://test-url.xyz"

@pytest.fixture
def feature_geojson():
    with open("tests/data/polygon_feature.geojson") as test_data:
        return json.load(test_data)

@pytest.fixture
def datestring():
    end_date = datetime.now()
    start_date = datetime(2015, 6, 22)
    return f"{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}"

def test_catalog_search_init(mocker, stac_url):
    mocker.patch("model.search_stac.SearchSTAC.connect_client", return_value=None)
    searcher = CatalogSearcher(stac_url)
    assert isinstance(searcher, CatalogSearcher)

def test_catalog_search(stac_url, feature_geojson, datestring, mocker):
    mocker.patch("model.search_stac.SearchSTAC.connect_client", return_value=None)
    mocker.patch("model.search_stac.SearchSTAC.get_items", return_value=[])
    searcher = CatalogSearcher(stac_url)
    params = {
        "feature_geojson": feature_geojson,
        "date_string": datestring,
        "max_cloud_cover": 100,
        "max_items": 3,
        "collection": "sentinel-2-l2a",
    }
    assert searcher.search_images(params) == []

def test_catalog_search(stac_url, feature_geojson, datestring, mocker):
    mocker.patch("model.search_stac.SearchSTAC.connect_client", return_value=None)
    mocker.patch("model.search_stac.SearchSTAC.get_items", return_value=[])
    searcher = CatalogSearcher(stac_url)
    params = {
        "feature_geojson": feature_geojson,
        "date_string": datestring,
        "max_cloud_cover": 100,
        "max_items": 3,
        "collection": "sentinel-1-grd",
    }
    assert searcher.search_images(params) == []


def test_catalog_search_platforms(stac_url, feature_geojson, datestring, mocker):
    mocker.patch("model.search_stac.SearchSTAC.connect_client", return_value=None)
    mocker.patch("model.search_stac.SearchSTAC.get_items", return_value=[])
    searcher = CatalogSearcher(stac_url,)
    params = {
        "feature_geojson": feature_geojson,
        "date_string": datestring,
        "max_cloud_cover": 100,
        "max_items": 3,
        "collection": "landsat-c2-l2",
        "platforms": ["landsat-5", "landsat-8"]
    }
    assert searcher.search_images(params) == []