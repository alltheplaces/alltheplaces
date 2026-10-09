import re
from itertools import groupby
from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS, DAYS_EN, OpeningHours
from locations.items import Feature


class JerseyPostJESpider(Spider):
    name = "jersey_post_je"
    item_attributes = {"operator": "Jersey Post", "operator_wikidata": "Q6184914"}
    allowed_domains = ["www.jerseypost.com"]

    async def start(self) -> AsyncIterator[JsonRequest]:
        # The post office and post box finder loads every location with one POST.
        yield JsonRequest("https://www.jerseypost.com/Umbraco/Surface/Tools/Locations/", data={})

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["data"]:
            # "Parade (St Helier)": the place, then its parish.
            m = re.fullmatch(r"(.*?)\s*\(([^)]+)\)\s*", location["name"]) or re.fullmatch(r"(.*)()", location["name"])
            place, parish = m.group(1).strip(), m.group(2).strip()
            if location.get("hasBox"):
                item = self.base_item(location, parish)
                item["ref"] = f"box-{location['id']}"
                item["extras"]["description"] = place
                if collection_times := self.parse_collection_times(location.get("collectionTimes") or []):
                    item["extras"]["collection_times"] = collection_times
                apply_category(Categories.POST_BOX, item)
                yield item
            if location.get("hasOffice"):
                item = self.base_item(location, parish)
                item["ref"] = f"office-{location['id']}"
                item["branch"] = re.sub(r"\s*Post Office$", "", place)
                item["phone"] = location.get("telephone")
                item["opening_hours"] = self.parse_office_hours(location.get("officeTimes") or [])
                apply_category(Categories.POST_OFFICE, item)
                yield item

    @staticmethod
    def base_item(location: dict, parish: str) -> Feature:
        item = Feature()
        item["lat"], item["lon"] = location["latitude"], location["longitude"]
        item["city"] = parish
        return item

    @staticmethod
    def days_of(text: str) -> list[str]:
        # "Monday - Friday" or "Saturday"
        first, _, last = (part.strip() for part in text.partition("-"))
        if first not in DAYS_EN or (last and last not in DAYS_EN):
            return []
        start, end = DAYS.index(DAYS_EN[first]), DAYS.index(DAYS_EN[last or first])
        return DAYS[start : end + 1]

    def parse_collection_times(self, rules: list[dict]) -> str:
        times = {}
        for rule in rules:
            for day in self.days_of(rule.get("day") or ""):
                times.setdefault(day, set()).update(re.findall(r"\d{1,2}:\d{2}", rule.get("times") or ""))
        by_day = {day: ",".join(sorted(t.zfill(5) for t in day_times)) for day, day_times in times.items()}
        out = []
        for time, days in groupby(DAYS, key=by_day.get):
            if time:
                days = list(days)
                out.append(f"{days[0]}-{days[-1]} {time}" if len(days) > 1 else f"{days[0]} {time}")
        return "; ".join(out)

    def parse_office_hours(self, counters: list[dict]) -> OpeningHours:
        oh = OpeningHours()
        for counter in counters[:1]:  # the post office counter itself
            # A later rule replaces an earlier one for its days, e.g. "Monday - Friday" then "Tuesday".
            day_times = {}
            for rule in counter.get("times") or []:
                for day in self.days_of(rule.get("day") or ""):
                    day_times[day] = rule.get("times") or ""
            for day, times in day_times.items():
                oh.add_ranges_from_string(f"{day} {times}")
        return oh
