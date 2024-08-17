from html import unescape

from locations.categories import Categories
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class PrestonsZASpider(WPStoreLocatorSpider):
    name = "prestons_za"
    item_attributes = {
        "brand": "Prestons",
        "brand_wikidata": "Q116861728",
        "extras": Categories.SHOP_ALCOHOL.value,
    }
    allowed_domains = ["prestonsliquors.co.za"]
    time_format = "%I:%M %p"

    def parse_item(self, item, location):
        item["branch"] = unescape(item.pop("name"))
        item["street_address"] = location.get("address")
        item.pop("addr_full", None)
        item["city"] = location.get("address2")
        yield item
