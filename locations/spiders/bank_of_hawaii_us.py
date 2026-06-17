from typing import Any

import scrapy
from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class BankOfHawaiiUSSpider(scrapy.Spider):
    name = "bank_of_hawaii_us"
    item_attributes = {"brand": "Bank of Hawaii", "brand_wikidata": "Q4856124"}
    allowed_domains = ["boh.com"]
    start_urls = ["https://www.boh.com/bohapi/get-locations?lat=21.33&lng=-157.845934&radius=250"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["locations"]:
            item = DictParser.parse(location)
            item["lat"] = location["geocode"]["latitude"]
            item["lon"] = location["geocode"]["longitude"]
            if "Branch" in location["type"]:
                if "In-Store Branch" in item["name"]:
                    item["located_in"] = item.pop("name").removesuffix(" In-Store Branch")
                else:
                    item["branch"] = item.pop("name").removesuffix(" Branch")
                apply_category(Categories.BANK, item)
                apply_yes_no(Extras.ATM, item, "Atm" in location["type"])
                item["opening_hours"] = self.parse_opening_hours(location["operationalHours"])
            # ATM only
            elif "Branch" not in location["type"] and "Atm" in location["type"]:
                apply_category(Categories.ATM, item)
            yield item

    def parse_opening_hours(self, rules) -> OpeningHours:
        oh = OpeningHours()
        for day_name, day in rules.items():
            if day["isClosed"]:
                oh.set_closed(day_name.title())
                continue
            for hours_range in day.get("openIntervals", []):
                # Times are in format "6 a.m.", "11:30 p.m.", etc. - normalize to include minutes
                start_time = hours_range["start"].replace(".", "").strip()
                end_time = hours_range["end"].replace(".", "").strip()
                # Add ":00" if no minutes specified
                if ":" not in start_time:
                    start_time = start_time.replace(" ", ":00 ")
                if ":" not in end_time:
                    end_time = end_time.replace(" ", ":00 ")
                oh.add_range(day_name.title(), start_time, end_time, time_format="%I:%M %p")
        return oh
