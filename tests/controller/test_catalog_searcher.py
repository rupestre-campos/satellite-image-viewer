import pytest
import json
from controller.catalog_searcher import CatalogSearcher
from app_config import AppConfig

from datetime import datetime

app_config_data = AppConfig()

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

def test_catalog_search(feature_geojson):
    searcher = CatalogSearcher(stac_url, feature_geojson)
    assert searcher.feature_geojson == feature_geojson

def test_catalog_search(stac_url, feature_geojson, datestring, mocker):
    mocker.patch("model.search_stac.SearchSTAC.connect_client", return_value=None)
    mocker.patch("model.search_stac.SearchSTAC.get_items", return_value=[])
    searcher = CatalogSearcher(stac_url, feature_geojson, datestring)
    assert searcher.search_images() == []