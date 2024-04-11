from locations.categories import Categories
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class SelfastZASpider(WPStoreLocatorSpider):
    name = "selfast_za"
    item_attributes = {"brand_wikidata": "Q116861449", "brand": "Selfast", "extras": Categories.SHOP_CLOTHES.value}
    allowed_domains = ["shop.selfast.co.za"]

    def parse_item(self, item, location):
        item.pop("street_address", None)
        yield item
