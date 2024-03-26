from model.search_stac import SearchSTAC

class CatalogSearcher:
    def __init__(self, stac_url, feature_geojson, date_string, max_cloud_cover=100, max_items=5):
        self.stac_url = stac_url
        self.feature_geojson = feature_geojson
        self.date_string = date_string
        self.max_cloud_cover = max_cloud_cover
        self.max_items = max_items

    def search_images(self):
        kwargs = {
            "datetime": self.date_string,
            "max_items":self.max_items,
            "query":{
                "eo:cloud_cover":{"lt":self.max_cloud_cover},
            }
        }
        stac_searcher = SearchSTAC(
            self.stac_url,
            feature_geojson=self.feature_geojson,
        )
        return stac_searcher.get_items(**kwargs)
