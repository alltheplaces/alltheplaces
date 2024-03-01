import re

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.storefinders.stockist import StockistSpider


class JoMercerAUSpider(StockistSpider):
    name = "jo_mercer_au"
    item_attributes = {"brand": "Jo Mercer", "brand_wikidata": "Q117961451"}
    key = "u3640"

    def parse_item(self, item, location):
        item.pop("email")
        hours_string = re.sub(r"\s+", " ", location["description"]).replace("Current Trading Hours:", "").strip()
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(hours_string)
        apply_category(Categories.SHOP_SHOES, item)
        yield item
