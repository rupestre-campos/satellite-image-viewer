from model.search_address import SearchAddress


def test_init_search_address():
    search_address = SearchAddress()
    assert isinstance(search_address, SearchAddress)

def test_search_address():
    test_address = "Sao paulo SP"
    search_address = SearchAddress()
    result = search_address.search_address(test_address)
    assert isinstance(result, tuple)
    assert result != (0,0)

def test_search_address_null():
    test_address = "teste1234-null"
    search_address = SearchAddress()
    result = search_address.search_address(test_address)
    assert isinstance(result, tuple)
    assert result == (0,0)