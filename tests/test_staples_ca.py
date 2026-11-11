from locations.categories import Categories
from locations.items import Feature
from locations.spiders.staples_ca import StaplesCASpider


def test_staples_ca_filters_wireless_services():
    spider = StaplesCASpider()

    store = Feature(ref="CA-104", name="Staples")
    results = list(spider.post_process_feature(store, {}))
    assert len(results) == 1
    assert results[0]["ref"] == "CA-104"
    assert results[0]["extras"] == Categories.SHOP_STATIONERY.value

    wireless = Feature(ref="CA-W-104", name="Staples Wireless")
    wireless_results = list(spider.post_process_feature(wireless, {}))
    assert len(wireless_results) == 0
