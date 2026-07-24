from typing import Any, Iterable

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import OpeningHours
from locations.items import Feature
from locations.storefinders.where2getit import Where2GetItSpider


class TacoJohnsUSSpider(Where2GetItSpider):
    name = "taco_johns_us"
    item_attributes = {"brand": "Taco John's", "brand_wikidata": "Q7673962"}
    api_brand_name = "tacojohns"
    api_key = "A3C026D8-26A4-11EE-8F79-C44648F5510E"

    def parse_item(self, item: Feature, location: dict, **kwargs: Any) -> Iterable[Feature]:
        item["branch"] = item.pop("name", None)
        item.pop("email", None)

        oh = OpeningHours()
        for day in ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"):
            open_time = location.get(f"{day}_open")
            close_time = location.get(f"{day}_close")
            if open_time and close_time:
                oh.add_range(day, open_time, close_time)
        item["opening_hours"] = oh

        apply_yes_no(Extras.DRIVE_THROUGH, item, location.get("drive_thru") == "1")
        apply_yes_no(Extras.DELIVERY, item, location.get("delivery") == "1")
        apply_category(Categories.FAST_FOOD, item)
        yield item
