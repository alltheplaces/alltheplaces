from typing import Iterable

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature, set_closed
from locations.storefinders.stockist import StockistSpider


class BuffaloExchangeUSSpider(StockistSpider):
    name = "buffalo_exchange_us"
    item_attributes = {
        "brand_wikidata": "Q4985721",
        "brand": "Buffalo Exchange",
    }
    key = "map_v3jk2neq"

    def parse_item(self, item: Feature, location: dict) -> Iterable[Feature]:
        location_description = location.get("description") or ""
        if "Permanently Closed" in location_description.title():
            set_closed(item)
        if branch_name := item.pop("name", None):
            item["branch"] = branch_name.removeprefix("Buffalo Outlet ")
        item["opening_hours"] = self.parse_opening_hours(location_description)
        apply_category(Categories.SHOP_CLOTHES, item)
        yield item

    def parse_opening_hours(self, location_hours: str) -> OpeningHours:
        opening_hours = OpeningHours()
        opening_hours.add_ranges_from_string(location_hours)
        return opening_hours
