from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

import scrapy
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_EN, OpeningHours
from locations.items import Feature

STOCKHOLM_TZ = ZoneInfo("Europe/Stockholm")


class CitygrossSESpider(scrapy.Spider):
    name = "citygross_se"
    item_attributes = {"brand": "City Gross", "brand_wikidata": "Q10453555"}
    start_urls = ["https://www.citygross.se/api/v1/PageData/stores"]
    custom_settings = {
        "DEFAULT_REQUEST_HEADERS": {
            "Referer": "https://www.citygross.se/",
        }
    }

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for entry in response.json():
            store = entry["data"]
            item = Feature()
            item["ref"] = store["id"]
            item["branch"] = store["storeName"].removeprefix("City Gross ")
            item["street_address"] = store["address"]["streetAddress"]
            item["postcode"] = store["address"]["zipCode"].strip()
            item["city"] = store["address"]["city"]
            item["country"] = "SE"
            item["phone"] = store.get("contactInformation", {}).get("phone", "").strip() or None
            item["email"] = store.get("contactInformation", {}).get("email", "").strip() or None
            item["website"] = "https://www.citygross.se" + store["url"]

            lat, lon = store["storeLocation"]["coordinates"].split(",")
            item["lat"] = float(lat)
            item["lon"] = float(lon)

            if hours := store.get("openingHours"):
                item["opening_hours"] = self.parse_opening_hours(hours)

            apply_category(Categories.SHOP_SUPERMARKET, item)
            yield item

    def _utc_to_local(self, iso_string: str | None) -> str | None:
        if not iso_string:
            return None
        dt = datetime.fromisoformat(iso_string.replace("Z", "+00:00"))
        return dt.astimezone(STOCKHOLM_TZ).strftime("%H:%M")

    def parse_opening_hours(self, hours: dict) -> OpeningHours:
        oh = OpeningHours()
        for day_en, times in hours.items():
            day = DAYS_EN.get(day_en.title())
            if not day or not times:
                continue
            opens = self._utc_to_local(times.get("opens"))
            closes = self._utc_to_local(times.get("closes"))
            if opens and closes:
                oh.add_range(day, opens, closes)
            else:
                oh.set_closed(day)
        return oh
