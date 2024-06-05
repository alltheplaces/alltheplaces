from locations.hours import DAYS_DE
from locations.items import Feature
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class MarkgrafenGetraenkemarktDESpider(WPStoreLocatorSpider):
    name = "markgrafen_getraenkemarkt_de"
    item_attributes = {
        "brand_wikidata": "Q100324493",
        "brand": "Markgrafen Getränkemarkt",
    }
    allowed_domains = [
        "www.markgrafen.com",
    ]
    days = DAYS_DE

    def parse_item(self, item: Feature, location: dict, **kwargs):
        if item["phone"]:
            item["phone"] = item["phone"].replace("/", "")

        yield item
