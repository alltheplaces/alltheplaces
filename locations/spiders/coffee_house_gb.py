from typing import Iterable

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.storefinders.stockist import StockistSpider


class CoffeeHouseGBSpider(StockistSpider):
    name = "coffee_house_gb"
    item_attributes = {"brand": "Coffee House", "brand_wikidata": "Q141791435"}
    key = "map_r3mnn4vq"

    def parse_item(self, item: Feature, location: dict) -> Iterable[Feature]:
        item["branch"] = (item.pop("name") or "").removeprefix("Coffee House ")
        hours_string = location["custom_fields"][0]["value"]
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(hours_string)
        apply_category(Categories.COFFEE_SHOP, item)
        yield item
