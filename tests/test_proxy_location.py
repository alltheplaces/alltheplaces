from locations.middlewares.zyte_api_by_country import get_proxy_location


def test_override():
    assert get_proxy_location("ie", "greggs_gb") == "ie"


def test_default():
    assert get_proxy_location(True, "greggs") is None


def test_spider_name():
    assert get_proxy_location(True, "greggs_gb") == "gb"
