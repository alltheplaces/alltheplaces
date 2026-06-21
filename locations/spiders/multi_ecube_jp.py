from datetime import date
from typing import AsyncIterator, Iterable

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature


class MultiEcubeJPSpider(Spider):
    name = "multi_ecube_jp"
    item_attributes = {
        "brand": "Multi-Ecube",
    }
    LIMIT = 20

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield self._make_request(1)

    def _make_request(self, page_no: int) -> JsonRequest:
        today = date.today().isoformat()
        url = (
            f"https://api.multiecube.com/v1/location/ph2"
            f"?includes_premium=true&limit={self.LIMIT}&page_no={page_no}"
            f"&service_type=1,2,3&includes_no_empty=true"
            f"&end_at={today}&from_at={today}&lang=ja"
        )
        return JsonRequest(url=url, callback=self.parse, cb_kwargs={"page_no": page_no})

    def parse(self, response: Response, page_no: int = 1, **kwargs) -> Iterable[Feature | JsonRequest]:
        data = response.json()
        for location in data.get("locations", []):
            yield from self.parse_location(location)
        page_total = data.get("page_total", 1)
        if page_no < page_total:
            yield self._make_request(page_no + 1)

    def parse_location(self, location: dict) -> Iterable[Feature]:
        item = Feature()
        item["ref"] = str(location["id"])
        item["lat"] = location.get("latitude")
        item["lon"] = location.get("longitude")
        item["country"] = "JP"

        attributes = location.get("attributes", {})
        item["branch"] = attributes.get("display_name")

        bh = attributes.get("business_hours", {})
        item["opening_hours"] = self._parse_hours(bh)

        images = attributes.get("images", [])
        for img in images:
            if img.get("type") == "1":
                item["image"] = img["url"]
                break

        apply_category(Categories.LUGGAGE_LOCKER, item)
        yield item

    def _parse_hours(self, bh: dict) -> OpeningHours:
        oh = OpeningHours()
        day_map = {
            "mon": "Mo",
            "tue": "Tu",
            "wed": "We",
            "thu": "Th",
            "fri": "Fr",
            "sat": "Sa",
            "sun": "Su",
        }
        for key, day in day_map.items():
            day_data = bh.get(key, {})
            open_time = day_data.get("open_time")
            close_time = day_data.get("close_time")
            if not open_time or not close_time:
                continue
            if open_time == "00:00" and close_time == "00:00":
                # "初電～終電" — open from first to last train; treat as 24/7
                oh.add_range(day, "00:00", "23:59")
            else:
                oh.add_range(day, open_time, close_time)
        return oh
