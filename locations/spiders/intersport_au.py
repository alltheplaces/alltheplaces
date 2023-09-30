from locations.items import Feature
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class IntersportAUSpider(WPStoreLocatorSpider):
    name = "intersport_au"
    item_attributes = {"brand": "Intersport", "brand_wikidata": "Q666888"}
    allowed_domains = ["intersport.com.au"]
    time_format = "%I:%M %p"

    def parse_item(self, item: Feature, location: dict, **kwargs):
        item["website"] = location["permalink"]
        yield item
