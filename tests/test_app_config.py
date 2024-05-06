import os
from app_config import AppConfig

def test_init():
    config = AppConfig()
    assert isinstance(config, AppConfig)

def test_without_sat():
    os.environ["ENABLE_SENTINEL"] = "False"
    os.environ["ENABLE_LANDSAT"] = "False"
    config = AppConfig()
    assert isinstance(config, AppConfig)

def test_with_all_sat():
    os.environ["ENABLE_SENTINEL"] = "True"
    os.environ["ENABLE_LANDSAT"] = "True"
    os.environ["ENABLE_SENTINEL1"] = "True"
    os.environ["ENABLE_DEM"] = "True"
    config = AppConfig()
    assert isinstance(config, AppConfig)
