import re
from typing import Iterable

from locations.categories import Categories, apply_category
from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature
from locations.storefinders.where2getit import Where2GetItSpider


class VansSpider(Where2GetItSpider):
    name = "vans"
    item_attributes = {"brand": "Vans", "brand_wikidata": "Q1135366"}
    api_brand_name = "vans"
    api_key = "E26F7F58-E275-11EF-9BFA-CC4AB53C2251"
    api_filter = {"or": {"off": {"eq": "TRUE"}, "out": {"eq": "TRUE"}}}

    def parse_item(self, item: Feature, location: dict, **kwargs) -> Iterable[Feature]:
        item["website"] = location.get("localurl")
        item["branch"] = re.sub(
            r"(?i)^vans\b[\s\-]*(?:(?:store|outlet|partner|retail|wholesale|trad|sis|vans)\b[\s\-]*)*",
            "",
            item.pop("name", ""),
        ).strip()

        oh = OpeningHours()
        for day in DAYS_FULL:
            open_time = location.get(f"{day.lower()}_open")
            close_time = location.get(f"{day.lower()}_close")
            if open_time and close_time:
                oh.add_range(day, open_time, close_time)
        item["opening_hours"] = oh
        apply_category(Categories.SHOP_SHOES, item)

        yield item
