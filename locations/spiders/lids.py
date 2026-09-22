import re
from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import Request, Response

from locations.categories import Categories, apply_category
from locations.hours import CLOSED_EN, DAYS_EN, DAYS_FULL, OpeningHours
from locations.items import Feature
from locations.user_agents import BROWSER_DEFAULT

TIME_PATTERN = re.compile(r"^(\d{1,2}):(\d{2})\s*(AM|PM)?$", re.IGNORECASE)
MISSING_VALUES = ["", "-999"]


class LidsSpider(Spider):
    name = "lids"
    item_attributes = {"brand": "Lids", "brand_wikidata": "Q19841609"}
    allowed_domains = ["lids.com"]
    custom_settings = {
        "COOKIES_ENABLED": True,
        "USER_AGENT": BROWSER_DEFAULT,
    }

    async def start(self) -> AsyncIterator[Request]:
        url = "https://www.lids.com/api/data/v2/stores/514599?lat=30.2729209&long=-97.74438630000002&num=12000&shipToStore=false"
        headers = {"Accept": "application/json", "Host": "www.lids.com"}
        yield Request(url, method="GET", headers=headers)

    @staticmethod
    def clean_value(value: Any) -> str | None:
        if not isinstance(value, str) or value.strip() in MISSING_VALUES:
            return None
        return value.strip()

    @staticmethod
    def parse_time(value: str) -> str | None:
        # Times are a mix of 12h and 24h clock readings, both carrying a meridiem, e.g. "9:00 PM" and "21:00 PM".
        if not (match := TIME_PATTERN.match(value)):
            return None
        hour, minute, meridiem = int(match.group(1)), match.group(2), (match.group(3) or "").upper()
        if meridiem and hour <= 12:
            hour = hour % 12 + (12 if meridiem == "PM" else 0)
        return f"{hour:02d}:{minute}"

    @staticmethod
    def parse_coordinates(coordinate: dict) -> tuple[float | None, float | None]:
        lat, lon = coordinate.get("latitude"), coordinate.get("longitude")
        if lat is None or lon is None:
            return None, None
        # The API currently reports latitude and longitude the wrong way round for all but a handful of stores.
        if not 0 < float(lat) < 90:
            lat, lon = lon, lat
        return lat, lon

    def parse_hours(self, location: dict) -> OpeningHours:
        opening_hours = OpeningHours()
        for day in DAYS_FULL:
            open_value = self.clean_value(location.get(day.lower() + "Open")) or ""
            close_value = self.clean_value(location.get(day.lower() + "Close")) or ""
            if open_value.lower() in CLOSED_EN and close_value.lower() in CLOSED_EN:
                opening_hours.set_closed(DAYS_EN[day])
                continue
            open_time = self.parse_time(open_value)
            close_time = self.parse_time(close_value)
            if open_time and close_time:
                opening_hours.add_range(DAYS_EN[day], open_time, close_time)
        return opening_hours

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json():
            item = Feature()
            item["ref"] = location["storeId"]
            item["branch"] = self.clean_value(location["location"].get("name"))
            item["street_address"] = self.clean_value(location["address"].get("addressLine1"))
            item["city"] = self.clean_value(location["address"].get("city"))
            item["postcode"] = self.clean_value(location["address"].get("zip"))
            item["state"] = self.clean_value(location["address"].get("state"))
            item["country"] = self.clean_value(location["address"].get("country"))
            item["phone"] = self.clean_value(location.get("phone"))
            item["website"] = self.clean_value(location.get("url"))
            item["lat"], item["lon"] = self.parse_coordinates(location["location"].get("coordinate") or {})
            item["opening_hours"] = self.parse_hours(location)

            apply_category(Categories.SHOP_CLOTHES, item)

            yield item
