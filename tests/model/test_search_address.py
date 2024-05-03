from model.search_address import SearchAddress


def test_init_search_address():
    search_address = SearchAddress(
        api_url="https://nominatim.openstreetmap.org/search", api_key="abcd")
    assert isinstance(search_address, SearchAddress)

def test_search_address(requests_mock):
    test_address = "Sao paulo SP"
    api_key = "abcd"
    requests_mock.get(
        f"https://nominatim.openstreetmap.org/search?api_key={api_key}&q={test_address}&format=json",
        json=[{"lat":1,"lon":1}]
    )
    search_address = SearchAddress(
        api_url="https://nominatim.openstreetmap.org/search", api_key=api_key)
    result = search_address.search_address(test_address)
    assert isinstance(result, tuple)
    assert result != (0,0)

def test_search_address_null():
    test_address = "teste1234-null"
    search_address = SearchAddress(
        api_url="https://nominatim.openstreetmap.org/search.bad", api_key="abcd")
    result = search_address.search_address(test_address)
    assert isinstance(result, tuple)
    assert result == (0,0)