import pytest
import json
from main import main


@pytest.fixture
def feature_geojson():
    with open("tests/data/polygon_feature.geojson") as test_data:
        return json.load(test_data)

def test_main_page():
    return_value = main()
    assert return_value == True

def test_main_draw_on_map(mocker, feature_geojson):
    mocker.patch(
        "view.web_map.WebMap.render_web_map",
        return_value={"geometry": feature_geojson}
    )
    mocker.patch.dict(
        "streamlit.session_state",
        {"image_data": {}}
    )
    return_value = main()
    assert return_value == True