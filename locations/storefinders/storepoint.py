import re

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours


class StorepointSpider(Spider):
    dataset_attributes = {"source": "api", "api": "storepoint.co"}

    key = ""

    custom_settings = {"ROBOTSTXT_OBEY": False}

    def start_requests(self):
        yield JsonRequest(url=f"https://api.storepoint.co/v1/{self.key}/locations")

    def parse_hours_for_day_12h(self, oh, day, hours_for_day):
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

    def parse_hours_for_day_24h(self, oh, day, hours_for_day):
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

    def parse_hours(self, location):
        oh = OpeningHours()
        for day in DAYS_FULL:
            if hours_for_day := location.get(day.lower()):
                if len(re.findall(r"(?:AM|PM)", hours_for_day, flags=re.IGNORECASE)) > 0:
                    self.parse_hours_for_day_12h(oh, day, hours_for_day)
                else:
                    self.parse_hours_for_day_24h(oh, day, hours_for_day)
        return oh.as_opening_hours()

    def parse(self, response, **kwargs):
        if not response.json()["success"]:
            return

        for location in response.json()["results"]["locations"]:
            item = DictParser.parse(location)

            item["lat"] = location["loc_lat"]
            item["lon"] = location["loc_long"]

            item["addr_full"] = item.pop("street_address")

            item["opening_hours"] = self.parse_hours(location)

            yield from self.parse_item(item, location)

    def parse_item(self, item, location: {}, **kwargs):
        yield item
