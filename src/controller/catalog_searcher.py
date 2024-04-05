from model.search_stac import SearchSTAC

class CatalogSearcher:
    def __init__(
            self,
            stac_url
        ):
        self.stac_url = stac_url
        self.search_stac = SearchSTAC(stac_url=self.stac_url)

    def search_images(self, params):
        feature_geojson = params.get("feature_geojson",{})
        geometry = feature_geojson.get("geometry")
        kwargs = {
            "datetime": params.get("date_string"),
            "max_items": params.get("max_items"),
            "collections": [params.get("collection")],
            "intersects": geometry,
            "query":{
                "eo:cloud_cover":{"lte":params.get("max_cloud_cover")},
            }
        }
        if params.get("platforms"):
            kwargs["query"].update({"platform":{"in": params.get("platforms")}})

        return self.search_stac.get_items(**kwargs)
