import re
from typing import AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours

TIME_RANGE = re.compile(r"(\d{1,2}[.:]\d{2})\s*[–-]\s*(\d{1,2}[.:]\d{2})")
LUNCH_BREAK = re.compile(r"перерыв:\s*(\d{1,2}[.:]\d{2})\s*[–-]\s*(\d{1,2}[.:]\d{2})")
DAY_FLAGS = {
    "Mo": "workingMonday",
    "Tu": "workingTuesday",
    "We": "workingWednesday",
    "Th": "workingThursday",
    "Fr": "workingFriday",
    "Sa": "workingSaturday",
    "Su": "workingSunday",
}


class RosselkhozbankRUSpider(Spider):
    name = "rosselkhozbank_ru"
    item_attributes = {"brand_wikidata": "Q3920226"}

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest("https://www.rshb.ru/api/v1/regions", callback=self.parse_regions)

    def parse_regions(self, response):
        for region in response.json():
            yield JsonRequest(
                f"https://www.rshb.ru/api/v1/branchesAndRemoteWorkplaces?regionCode={region['code']}",
            )

    def parse(self, response):
        for poi in response.json()["branches"]:
            item = DictParser.parse(poi)
            item["branch"] = item.pop("name")
            item["lat"], item["lon"] = poi.get("gpsLatitude"), poi.get("gpsLongitude")
            self.parse_hours(item, poi)
            apply_category(Categories.BANK, item)
            yield item

    def parse_hours(self, item, poi):
        work_schedule = poi.get("workSchedule") or {}
        oh = OpeningHours()
        for day, flag in DAY_FLAGS.items():
            if not work_schedule.get(flag):
                continue
            saturday = day == "Sa"
            time_ranges = TIME_RANGE.findall(work_schedule.get("workTimeSaturday" if saturday else "workTime") or "")
            if len(time_ranges) != 1:
                continue
            open_time, close_time = (t.replace(".", ":") for t in time_ranges[0])
            lunch = LUNCH_BREAK.search(work_schedule.get("lunchHourSaturday" if saturday else "lunchHour") or "")
            if lunch:
                oh.add_range(day, open_time, lunch.group(1).replace(".", ":"))
                oh.add_range(day, lunch.group(2).replace(".", ":"), close_time)
            else:
                oh.add_range(day, open_time, close_time)
        item["opening_hours"] = oh
