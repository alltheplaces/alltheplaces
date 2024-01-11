import re

from locations.categories import Categories
from locations.hours import OpeningHours
from locations.storefinders.stockist import StockistSpider


class ForcastAUSpider(StockistSpider):
    name = "forcast_au"
    item_attributes = {"brand": "Forcast", "brand_wikidata": "Q118384540", "extras": Categories.SHOP_CLOTHES.value}
    key = "u7172"

    def parse_item(self, item, location):
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(re.sub(r"\s+", " ", location["description"]))
        yield item
