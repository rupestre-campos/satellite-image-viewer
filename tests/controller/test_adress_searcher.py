from controller.address_searcher import AddressSearcher


def test_init_address_searcher():
    address_searcher = AddressSearcher(api_url="https://nominatim.openstreetmap.org/search.php", api_key="abcd")
    assert isinstance(address_searcher, AddressSearcher)

def test_search_address(mocker):
    test_value = "Sao paulo sp"
    mocker.patch(
        "model.search_address.SearchAddress.search_address",
        return_value=(100,200)
    )
    address_searcher = AddressSearcher(api_url="https://nominatim.openstreetmap.org/search.php", api_key="abcd")

    result = address_searcher.search_address(test_value)
    assert isinstance(result, tuple)

def test_search_address_eerror(mocker):
    test_value = "teste 123 xysz"
    mocker.patch(
        "model.search_address.SearchAddress.search_address",
        return_value=(0,0)
    )
    address_searcher = AddressSearcher(api_url="https://nominatim.openstreetmap.org/search.php", api_key="abcd")

    result = address_searcher.search_address(test_value)
    assert isinstance(result, tuple)
