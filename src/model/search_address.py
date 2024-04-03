from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter


class SearchAddress:
    def __init__(self, user_agent="test-app", timeout=3, min_delay_seconds=2):
        self.geolocator = self.__create_nominatim_geolocator(timeout, user_agent)
        self.geocode = self.__add_rate_limiter(self.geolocator.geocode, min_delay_seconds)

    @staticmethod
    def __create_nominatim_geolocator(timeout, user_agent):
        return Nominatim(timeout=timeout,user_agent=user_agent)

    @staticmethod
    def __add_rate_limiter(geocode, min_delay_seconds):
        return RateLimiter(geocode, min_delay_seconds=min_delay_seconds)

    def search_address(self, address):
        location = self.geocode(address)
        if location:
            return (location.latitude, location.longitude)
        return (0,0)
