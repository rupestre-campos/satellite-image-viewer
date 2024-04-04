from model.search_address import SearchAddress

class AddressSearcher:
    def __init__(self, api_url, api_key):
        self.geolocator = SearchAddress(
            api_url=api_url,
            api_key=api_key
        )

    def search_address(self, address):
        return self.geolocator.search_address(address)