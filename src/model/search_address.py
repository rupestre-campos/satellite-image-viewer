import requests
from requests.adapters import HTTPAdapter, Retry


class SearchAddress:
    def __init__(self, api_url, api_key):
        self.api_url = api_url
        self.api_key = api_key
        self.session = self.__get_session()

    @staticmethod
    def __get_session():
        session = requests.Session()

        retries = Retry(total=5,
                        backoff_factor=0.1,
                        status_forcelist=[ 500, 502, 503, 504 ])

        session.mount("https://", HTTPAdapter(max_retries=retries))
        return session

    def __geocode(self, address):
        params = {
            "api_key": self.api_key,
            "q": address,
            "format": "json"
        }
        response = self.session.get(self.api_url, params=params)
        if response.ok:
            return response.json()
        return {}

    def search_address(self, address):
        location = self.__geocode(address)
        if location:
            return (location[0].get("lat", 0), location[0].get("lon", 0))
        return (0,0)
