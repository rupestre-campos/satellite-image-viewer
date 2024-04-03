from model.search_address import SearchAddress

class AddressSearcher:
    def __init__(self, user_agent="test-app", timeout=3, min_delay_seconds=2):
        self.geolocator = SearchAddress(
            timeout=timeout,
            user_agent=user_agent,
            min_delay_seconds=min_delay_seconds)

    def search_address(self, address):
        return self.geolocator.search_address(address)