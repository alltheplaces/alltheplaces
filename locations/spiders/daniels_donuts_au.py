import re

from locations.hours import DAYS_FULL, OpeningHours
from locations.storefinders.storepoint import StorepointSpider


class DanielsDonutsAUSpider(StorepointSpider):
    name = "daniels_donuts_au"
    item_attributes = {"brand": "Daniel's Donuts", "brand_wikidata": "Q116147181"}
    key = "1614a61b80e685"

    def parse_item(self, item, location: {}, **kwargs):
        item["addr_full"] = item.pop("street_address")

        item["opening_hours"] = OpeningHours()
        for day in DAYS_FULL:
            if times := location.get(day.lower()):
                for start_hour, start_min, start_am_pm, end_hour, end_min, end_am_pm in re.findall(
                    r"(\d{1,2})(?:[:\.](\d{2}))?\s*(AM|PM)\s*-\s*(\d{1,2})(?:[:\.](\d{2}))?\s*(AM|PM)",
                    times,
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
                    item["opening_hours"].add_range(day, start_time, end_time, time_format="%I:%M %p")
        yield item
