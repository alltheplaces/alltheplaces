import re

from locations.storefinders.sweetiq import SweetIQSpider


class SizzlerSpider(SweetIQSpider):
    name = "sizzler"
    item_attributes = {"brand": "Sizzler", "brand_wikidata": "Q1848822"}
    start_urls = ["https://locations.sizzler.com/"]

    def parse_item(self, item, location):
        item["name"] = re.sub(r" - (?:Now|Delivery|Newly) .*", "", item["name"])
        item.pop("email")
        item.pop("website")
        yield item
