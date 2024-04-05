from pystac_client import Client


class SearchSTAC:
    def __init__(self, stac_url):
        self.stac_url = stac_url
        self.client = self.connect_client(self.stac_url)

    @staticmethod
    def connect_client(stac_url):
        return Client.open(stac_url)

    def __get_items(self, **kwargs):
        return self.client.search(
            **kwargs
        ).item_collection()

    def get_items(self, **kwargs):
        return [item.to_dict() for item in self.__get_items(**kwargs)]
