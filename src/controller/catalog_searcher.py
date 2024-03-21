from model.search_stac import SearchSTAC

class CatalogSearcher:
    def __init__(self, stac_url, feature_geojson):
        self.stac_url = stac_url
        self.feature_geojson = feature_geojson

    def search_images(self):
        stac_searcher = SearchSTAC(
            self.stac_url,
            feature_geojson=self.feature_geojson
        )
        return stac_searcher.get_items()
