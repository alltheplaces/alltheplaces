from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.items import Feature

# Just Salad publishes every location in a single JSON file on its CDN. The
# feed carries a states lookup table which the address blocks reference by
# numeric id, and rows for stores that have not opened yet, flagged by
# "coming_soon".


class JustSaladUSSpider(Spider):
    name = "just_salad_us"
    item_attributes = {"brand": "Just Salad", "brand_wikidata": "Q23091823"}
    allowed_domains = ["cdn1.justsalad.com"]
    start_urls = ["https://cdn1.justsalad.com/public/store_locations.json"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        data = response.json()
        states = {state["id"]: state["abbreviation"] for state in data["states"]}

        for location in data["storelocations"]:
            if location.get("coming_soon") or location.get("business_status") != "OPERATIONAL":
                continue

            item = DictParser.parse(location["address"])
            item["ref"] = location["store_num"]
            item["branch"] = location["name"]
            item["phone"] = location.get("phone")
            item["state"] = states.get(location["address"].get("state"))
            item["street_address"] = " ".join(
                filter(None, [location["address"].get("address_1"), location["address"].get("address_2")])
            )

            item["opening_hours"] = OpeningHours()
            for period in location.get("opening_hours", {}).get("periods", []):
                if period["open"]["time"] == period["close"]["time"] == "0000":
                    item["opening_hours"].set_closed(DAYS[period["open"]["day"]])
                else:
                    item["opening_hours"].add_range(
                        DAYS[period["open"]["day"]],
                        period["open"]["time"],
                        period["close"]["time"],
                        time_format="%H%M",
                    )

            amenities = location.get("amenities") or {}
            apply_yes_no(Extras.DRIVE_THROUGH, item, amenities.get("drive_thru") is True)
            apply_yes_no(Extras.OUTDOOR_SEATING, item, amenities.get("outdoor_seat") is True)

            apply_category(Categories.FAST_FOOD, item)
            item["extras"]["cuisine"] = "salad"

            yield item
