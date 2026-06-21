from datetime import date
from typing import Any, AsyncIterator, Iterable

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.hours import OpeningHours
from locations.items import Feature


class MultiecubeJPSpider(Spider):
    name = "multiecube_jp"
    item_attributes = {"brand": "Multi-Ecube"}
    custom_settings = {"ROBOTSTXT_OBEY": False}

    DAY_MAP = {
        "mon": "Mo",
        "tue": "Tu",
        "wed": "We",
        "thu": "Th",
        "fri": "Fr",
        "sat": "Sa",
        "sun": "Su",
    }

    def _api_url(self, page: int) -> str:
        today = date.today().isoformat()
        return (
            f"https://api.multiecube.com/v1/location/ph2"
            f"?includes_premium=true&limit=20&page_no={page}"
            f"&service_type=1,2,3&includes_no_empty=true"
            f"&end_at={today}&from_at={today}&lang=ja"
        )

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(self._api_url(1), callback=self.parse_page)

    def parse_page(self, response: Response, **kwargs: Any) -> Iterable[Any]:
        data = response.json()
        for location in data.get("locations", []):
            yield from self.parse_location(location)

        page_no = data.get("page_no", 1)
        page_total = data.get("page_total", 1)
        if page_no < page_total:
            yield JsonRequest(self._api_url(page_no + 1), callback=self.parse_page)

    def parse_location(self, location: dict) -> Iterable[Feature]:
        attrs = location.get("attributes", {})

        item = Feature()
        item["ref"] = str(location["id"])
        item["branch"] = attrs.get("display_name")
        item["lat"] = location.get("latitude")
        item["lon"] = location.get("longitude")
        item["country"] = "JP"
        item["extras"]["amenity"] = "luggage_locker"

        bh = attrs.get("business_hours", {})
        # Only parse hours when individual day entries have real times
        # (not "00:00"/"00:00" which means "first train to last train")
        oh = OpeningHours()
        has_specific_hours = False
        for api_day, osm_day in self.DAY_MAP.items():
            day_data = bh.get(api_day, {})
            open_time = day_data.get("open_time")
            close_time = day_data.get("close_time")
            if open_time and close_time and not (open_time == "00:00" and close_time == "00:00"):
                oh.add_range(osm_day, open_time, close_time)
                has_specific_hours = True
        if has_specific_hours:
            item["opening_hours"] = oh

        yield item
