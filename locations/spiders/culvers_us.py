import json
from datetime import datetime
from typing import Any, Iterable

import scrapy
from scrapy import Request
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.geo import city_locations
from locations.hours import OpeningHours
from locations.items import set_closed


class CulversUSSpider(scrapy.Spider):
    name = "culvers_us"
    item_attributes = {"brand": "Culver's", "brand_wikidata": "Q1143589"}

    async def start(self) -> Iterable[Request]:
        for city in city_locations("US", 100000):
            yield JsonRequest(
                url=f'https://www.culvers.com/api/locator/getLocations?lat={city["latitude"]}&long={city["longitude"]}&radius=600000&limit=10000'
            )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["data"]["geofences"]:
            location.update(location.pop("metadata"))
            location.pop("geometry")
            item = DictParser.parse(location)
            item["ref"] = location["restaurantNumber"]
            item["name"] = self.item_attributes["brand"]
            item["lon"], item["lat"] = location["geometryCenter"]["coordinates"]
            item["website"] = "https://www.culvers.com/restaurants/" + location["slug"]

            apply_category(Categories.FAST_FOOD, item)

            if location.get("isTemporarilyClosed"):
                set_closed(item)

            if dine_in_hours := self.parse_hours(location.get("dineInHours")):
                item["opening_hours"] = dine_in_hours

            has_drive_through = bool(location.get("driveThruHours"))
            apply_yes_no(Extras.DRIVE_THROUGH, item, has_drive_through)
            if has_drive_through:
                if drive_through_hours := self.parse_hours(location.get("driveThruHours")):
                    item["extras"]["opening_hours:drive_through"] = drive_through_hours.as_opening_hours()

            if open_date := location.get("openDate"):
                try:
                    item["extras"]["start_date"] = datetime.strptime(open_date, "%m/%d/%Y").strftime("%Y-%m-%d")
                except ValueError:
                    pass

            yield item

    def parse_hours(self, raw_hours: str | None) -> OpeningHours | None:
        """
        Hours are provided as a JSON-encoded string keyed by day abbreviation
        plus "O"/"C" suffixes for open/close, e.g.:
        {"MoO": "10:00 AM", "MoC": "10:00 PM", "TuO": "10:00 AM", ...}
        """
        if not raw_hours:
            return None
        try:
            hours = json.loads(raw_hours)
        except (json.JSONDecodeError, TypeError):
            self.logger.warning("Failed to parse hours JSON: %s", raw_hours)
            return None

        oh = OpeningHours()
        for day in ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]:
            open_time = hours.get(f"{day}O")
            close_time = hours.get(f"{day}C")
            if not open_time or not close_time or open_time == "n/a" or close_time == "n/a":
                continue
            oh.add_range(day, open_time, close_time, time_format="%I:%M %p")
        return oh if oh else None
