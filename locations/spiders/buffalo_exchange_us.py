from typing import Iterable

from locations.categories import Categories, apply_category
from locations.hours import DAYS_EN, OpeningHours
from locations.items import Feature
from locations.storefinders.stockist import StockistSpider


class BuffaloExchangeUSSpider(StockistSpider):
    name = "buffalo_exchange_us"
    item_attributes = {
        "brand_wikidata": "Q4985721",
        "brand": "Buffalo Exchange",
    }
    key = "map_v3jk2neq"

    def parse_item(self, item: Feature, location: dict) -> Iterable[Feature]:
        hours_raw = location.get("description")
        if hours_raw and "permanently closed" in hours_raw.lower():
            return
        item["branch"] = item.pop("name").removeprefix("Buffalo Outlet ")
        item.pop("street_address")
        if hours_raw:
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(hours_raw, days=DAYS_EN)
        if "Headquarters" in item["branch"]:
            item["name"] = self.item_attributes["brand"]
            apply_category(Categories.OFFICE_COMPANY, item)
        else:
            apply_category(Categories.SHOP_CLOTHES, item)
        yield item
