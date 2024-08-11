import json
import re

from scrapy import Request, Spider
from scrapy.http import Response

from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature


class StoreLocatorWidgetsSpider(Spider):
    """
    Store Locator Widgets are a set of store locator components.
    https://www.storelocatorwidgets.com/api/

    To use, specify a `key`
    """

    dataset_attributes = {"source": "api", "api": "storelocatorwidgets.com"}
    key: str = ""

    def start_requests(self):
        yield Request(url=f"https://cdn.storelocatorwidgets.com/json/{self.key}")

    def parse_hours_for_day_12h(self, oh: OpeningHours, day: str, hours_for_day: str):
        hours_for_day = (
            hours_for_day.replace("midnight", "12AM").replace("midday", "12PM").replace("24 hours", "12AM - 11:59PM")
        )
        for start_hour, start_min, start_am_pm, end_hour, end_min, end_am_pm in re.findall(
            r"(\d{1,2})(?:[:\.](\d{2}))?\s*(AM|PM)\s*-\s*(\d{1,2})(?:[:\.](\d{2}))?\s*(AM|PM)",
            hours_for_day,
            flags=re.IGNORECASE,
        ):
            if len(start_hour) == 1:
                start_hour = "0" + start_hour
            if len(end_hour) == 1:
                end_hour = "0" + end_hour
            if start_min == "":
                start_min = "00"
            if end_min == "":
                end_min = "00"
            start_time = f"{start_hour}:{start_min} {start_am_pm}"
            end_time = f"{end_hour}:{end_min} {end_am_pm}"
            oh.add_range(day, start_time, end_time, time_format="%I:%M %p")

    def parse_hours_for_day_24h(self, oh: OpeningHours, day: str, hours_for_day: str):
        hours_for_day = (
            hours_for_day.replace("midnight", "00:00").replace("midday", "12:00").replace("24 hours", "00:00 - 23:59")
        )
        for start_hour, start_min, end_hour, end_min in re.findall(
            r"(\d{1,2})(?:[:\.](\d{2}))?\s*-\s*(\d{1,2})(?:[:\.](\d{2}))?",
            hours_for_day,
        ):
            if len(start_hour) == 1:
                start_hour = "0" + start_hour
            if len(end_hour) == 1:
                end_hour = "0" + end_hour
            if start_min == "":
                start_min = "00"
            if end_min == "":
                end_min = "00"
            start_time = f"{start_hour}:{start_min}"
            end_time = f"{end_hour}:{end_min}"
            oh.add_range(day, start_time, end_time, time_format="%H:%M")

    def parse_hours(self, location: dict) -> OpeningHours:
        oh = OpeningHours()
        for day in DAYS_FULL:
            if hours_for_day := location["data"].get("hours_" + day):
                if len(re.findall(r"(?:AM|PM)", hours_for_day, flags=re.IGNORECASE)) > 0:
                    self.parse_hours_for_day_12h(oh, day, hours_for_day)
                else:
                    self.parse_hours_for_day_24h(oh, day, hours_for_day)
        return oh.as_opening_hours()

    def parse(self, response: Response):
        data_clean = response.text[4 : len(response.text) - 1]
        locations = json.loads(data_clean)["stores"]
        for location in locations:
            item = DictParser.parse(location)
            item["ref"] = location["storeid"]
            item["lat"] = location["data"].get("map_lat")
            item["lon"] = location["data"].get("map_lng")
            item["addr_full"] = location["data"].get("address")
            if "phone" in location["data"]:
                item["phone"] = location["data"]["phone"]
            if "email" in location["data"]:
                item["email"] = location["data"]["email"]
            if "website" in location["data"]:
                item["website"] = location["data"]["website"]
            if "image" in location["data"]:
                item["image"] = location["data"]["image"]
            item["opening_hours"] = self.parse_hours(location)
            yield from self.parse_item(item, location)

    def parse_item(self, item: Feature, location: dict):
        yield item
