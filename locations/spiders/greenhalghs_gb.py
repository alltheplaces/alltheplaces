from locations.categories import Categories
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class GreenhalghsGBSpider(WPStoreLocatorSpider):
    name = "greenhalghs_gb"
    item_attributes = {"brand": "Greenhalgh's", "brand_wikidata": "Q99939079", "extras": Categories.SHOP_BAKERY.value}
    allowed_domains = ["www.greenhalghs.com"]
    time_format = "%I:%M %p"

    def parse_item(self, item, location):
        item.pop("addr_full", None)
        item["street_address"] = location.get("address2")
        if item["website"] and item["website"].startswith("/"):
            item["website"] = "https://www.greenhalghs.com" + item["website"]
        yield item
