import os


class AppConfig:
    def __init__(self):
        self.stac_url = os.getenv("STAC_URL", "https://earth-search.aws.element84.com/v1")