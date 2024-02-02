import re

from locations.categories import Categories
from locations.hours import OpeningHours
from locations.storefinders.stockist import StockistSpider


class RainsSpider(StockistSpider):
    name = "rains"
    item_attributes = {"brand": "Rains", "brand_wikidata": "Q119440481", "extras": Categories.SHOP_CLOTHES.value}
    key = "u11150"

    def parse_item(self, item, location):
        hours_string = re.sub(r"\s+", " ", location["description"])
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(hours_string)
        yield item
