from locations.categories import Categories
from locations.items import Feature
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class SwingKitchenSpider(WPStoreLocatorSpider):
    name = "swing_kitchen"
    item_attributes = {"brand": "Swing Kitchen", "brand_wikidata": "Q116943226", "extras": Categories.FAST_FOOD.value}
    allowed_domains = [
        "www.swingkitchen.com",
    ]

    def parse_item(self, item: Feature, location: dict, **kwargs):
        del item["addr_full"]
        del item["phone"]

        yield item
