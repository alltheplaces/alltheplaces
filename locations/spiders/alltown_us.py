from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class AlltownUSSpider(WPStoreLocatorSpider):
    name = "alltown_us"
    item_attributes = {
        "brand_wikidata": "Q119586667",
        "brand": "Alltown",
    }
    allowed_domains = [
        "alltown.com",
    ]
    time_format = "%I:%M %p"

    def parse_item(self, item: Feature, location: dict, **kwargs):
        apply_category(Categories.SHOP_CONVENIENCE, item)
        yield item
