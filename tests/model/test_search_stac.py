import pytest
import json
from model.search_stac import SearchSTAC
from app_config import AppConfig
from datetime import datetime

app_config_data = AppConfig()

@pytest.fixture
def stac_url():
    return app_config_data.stac_url

@pytest.fixture
def feature_geojson():
    with open("tests/data/polygon_feature.geojson") as test_data:
        return json.load(test_data)

@pytest.fixture
def datestring():
    end_date = datetime.now()
    start_date = datetime(2015, 6, 22)
    return f"{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}"

def test_init_search_stac(stac_url):
    stac_client = SearchSTAC(stac_url)
    assert isinstance(stac_client, SearchSTAC)

def test_search_stac(stac_url, feature_geojson, datestring):
    stac_client = SearchSTAC(stac_url)
    kwargs = {"datetime":datestring, "max_items":3, "intersects": feature_geojson}
    results = stac_client.get_items(**kwargs)
    assert isinstance(results, list)
