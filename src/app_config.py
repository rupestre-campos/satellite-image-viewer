import os


class AppConfig:
    def __init__(self):
        self.stac_url = os.getenv("STAC_URL", "https://earth-search.aws.element84.com/v1")
        self.google_basemap = os.getenv("GOOGLE_BASEMAP", "https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}")
        self.esri_basemap = os.getenv("ESRI_BASEMAP", "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}")
        self.max_area_hectares = int(os.getenv("MAX_AREA_HECTARES", 100_000))