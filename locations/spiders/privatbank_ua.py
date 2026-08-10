from typing import Any, AsyncIterator

from scrapy import Request, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_WEEKDAY, OpeningHours

ENDPOINT = "https://map.privatbank.ua/google_geo_coding_api.php"
# Map "objType" -> OSM category. NSI supplies name=ПриватБанк for banks/terminals; ATMs have no name.
CATEGORIES = {
    "branch": Categories.BANK,
    "atm": Categories.ATM,
    "terminal": {"amenity": "payment_terminal"},  # self-service payment terminals; no Categories enum
}


class PrivatbankUASpider(Spider):
    name = "privatbank_ua"
    item_attributes = {"brand": "ПриватБанк", "brand_wikidata": "Q1515015"}

    async def start(self) -> AsyncIterator[Any]:
        # The map search endpoint reads form-encoded POST params (a JSON body is ignored and returns a
        # single fallback point), so JsonRequest is not used. A bounding box over all of Ukraine at a
        # high zoom returns every point individually; machines sharing a coordinate stay grouped into
        # one point and yield a single POI.
        for obj_type in CATEGORIES:
            yield Request(
                ENDPOINT,
                method="POST",
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                body="lat1=53&lng1=40.5&lat2=44&lng2=22&zoom=20&type=" + obj_type,
                cb_kwargs={"obj_type": obj_type},
            )

    def parse(self, response: Response, obj_type: str, **kwargs: Any) -> Any:
        for point in response.json()["items"]:
            if point.get("is_active") != 1:
                continue  # closed or temporarily out of service
            item = DictParser.parse(point)  # maps id -> ref, lat/lng -> lat/lon
            item["opening_hours"] = self.parse_hours(point.get("work_time") or "")
            apply_category(CATEGORIES[obj_type], item)
            yield item

    @staticmethod
    def parse_hours(work_time: str) -> str | None:
        # Only branches carry hours, as 4x HHMM (Mon-Fri open, close, lunch-break start, lunch-break
        # end; "----" when absent). ATMs/terminals send an empty string. Weekends are not encoded.
        if len(work_time) != 16:
            return None
        open_time, close_time, break_start, break_end = (work_time[i : i + 4] for i in range(0, 16, 4))
        try:
            hours = OpeningHours()
            if break_start == "----":
                hours.add_days_range(DAYS_WEEKDAY, open_time, close_time, time_format="%H%M")
            else:
                hours.add_days_range(DAYS_WEEKDAY, open_time, break_start, time_format="%H%M")
                hours.add_days_range(DAYS_WEEKDAY, break_end, close_time, time_format="%H%M")
            return hours.as_opening_hours()
        except ValueError:
            return None
