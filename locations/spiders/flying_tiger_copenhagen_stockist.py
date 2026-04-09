from typing import Iterable

from locations.categories import Categories, apply_category
from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature
from locations.storefinders.stockist import StockistSpider


class FlyingTigerCopenhagenStockistSpider(StockistSpider):
    name = "flying_tiger_copenhagen_stockist"
    item_attributes = {
        "brand": "Flying Tiger Copenhagen",
        "brand_wikidata": "Q2786319",
    }
    key = "u7767"
    # Name is the address, not a branch name
    drop_attributes = {"name"}

    def parse_item(self, item: Feature, location: dict) -> Iterable[Feature]:
        oh = OpeningHours()
        for field in location.get("custom_fields", []):
            if field["name"] == "Store Number":
                item["ref"] = field["value"]
            elif field["name"] in DAYS_FULL:
                if field.get("value"):
                    oh.add_ranges_from_string(f"{field['name']} {field['value']}")
        item["opening_hours"] = oh
        apply_category(Categories.SHOP_VARIETY_STORE, item)
        yield item
