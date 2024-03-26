import os


class AppConfig:
    def __init__(self):
        self.stac_url = os.getenv("STAC_URL", "https://earth-search.aws.element84.com/v1")
        self.open_street_maps = os.getenv("OSM_BASEMAP", "https://tile.openstreetmap.org/{z}/{x}/{y}.png")
        self.google_basemap = os.getenv("GOOGLE_BASEMAP", "https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}")
        self.esri_basemap = os.getenv("ESRI_BASEMAP", "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}")
        self.max_area_hectares = int(os.getenv("MAX_AREA_HECTARES", 100_000))
        self.buffer_width = int(os.getenv("BUFFER_WIDTH", 10000))
        self.email = os.getenv("EMAIL", "test-satellite-viewer@null.com")
        self.default_start_address = os.getenv("DEFAULT_START_ADDRESS", "Ingaí MG")
