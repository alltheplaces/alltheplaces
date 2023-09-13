import re

from locations.hours import OpeningHours
from locations.storefinders.stockist import StockistSpider


class DangerfieldSpider(StockistSpider):
    name = "dangerfield"
    item_attributes = {"brand": "Dangerfield", "brand_wikidata": "Q119220880"}
    key = "u12223"

    def parse_item(self, item, location):
        if "DANGERFIELD NZ" in item["name"]:
            item["country"] = "NZ"
        else:
            item["country"] = "AU"
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(re.sub(r"\s+", " ", location.get("description")))
        yield item
