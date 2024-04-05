from model.search_address import SearchAddress


def test_init_search_address():
    search_address = SearchAddress(api_url="https://nominatim.openstreetmap.org/search", api_key="abcd")
    assert isinstance(search_address, SearchAddress)

def test_search_address():
    test_address = "Sao paulo SP"
    search_address = SearchAddress(api_url="https://nominatim.openstreetmap.org/search", api_key="abcd")
    result = search_address.search_address(test_address)
    assert isinstance(result, tuple)
    assert result != (0,0)

def test_search_address_null():
    test_address = "teste1234-null"
    search_address = SearchAddress(api_url="https://nominatim.openstreetmap.org/search.bad", api_key="abcd")
    result = search_address.search_address(test_address)
    assert isinstance(result, tuple)
    assert result == (0,0)