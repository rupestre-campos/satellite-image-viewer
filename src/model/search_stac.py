from pystac_client import Client

class SearchSTAC:
    def __init__(self, stac_url, feature_geojson={}):
        self.max_items = 10
        self.collection = "sentinel-2-l2a"
        self.stac_url = stac_url
        self.feature_geojson = feature_geojson
        self.client = self.connect_client()

    def connect_client(self):
        return Client.open(self.stac_url)

    def __get_collections(self):
        return self.client.get_collections()

    def __get_collection_info(self):
        return self.client.get_collection(self.collection)

    def __get_items(self):
        return self.client.search(
            collections=[self.collection],
            intersects=self.feature_geojson,
            max_items=self.max_items
        ).item_collection()

    def get_collections(self):
        return [collection.to_dict() for collection in self.__get_collections()]

    def get_collection_info(self):
        return self.__get_collection_info().to_dict()

    def get_items(self):
        return [item.to_dict() for item in self.__get_items()]
