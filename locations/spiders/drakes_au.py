from locations.items import Feature
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class DrakesAUSpider(WPStoreLocatorSpider):
    name = "drakes_au"
    item_attributes = {
        "brand_wikidata": "Q48988077",
        "brand": "Drakes",
    }
    allowed_domains = [
        "drakes.com.au",
    ]

    def parse_item(self, item: Feature, location: dict):
        item.pop("addr_full", None)
        item.pop("email", None)
        item.pop("website", None)
        yield item
