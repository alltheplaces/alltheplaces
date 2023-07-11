from html import unescape

from locations.storefinders.wp_store_locator import WPStoreLocatorSpider

class RolldAUSpider(WPStoreLocatorSpider):
    name = "rolld_au"
    item_attributes = {"brand": "Roll'd", "brand_wikidata": "Q113114631"}
    allowed_domains = ["rolld.com.au"]
    time_format = "%I:%M %p"

    def parse_item(self, item, location):
        item["name"] = unescape(item["name"])
        yield item
