import re
from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_WEEKDAY, OpeningHours

HOURS_RANGE = re.compile(r"^(\d{1,2}:\d{2})-(\d{1,2}:\d{2})$")


class PumbUASpider(Spider):
    name = "pumb_ua"
    item_attributes = {"brand": "ПУМБ", "brand_wikidata": "Q4341156"}

    async def start(self) -> AsyncIterator[Any]:
        yield JsonRequest(url="https://about.pumb.ua/home/getbankomats")

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["bankomats"]:
            if location.get("IsBankomatRadius"):
                continue  # shared "Radius" network ATMs operated by other banks, not PUMB
            if not self.valid_coordinates(location):
                continue  # a few feed rows have malformed Lat/Lng (e.g. "30.220-8", "51.510648, ")
            # DictParser maps Id->ref, Title->name, Lat/Lng->lat/lon, Address->addr_full, CityName->city
            item = DictParser.parse(location)
            item["street_address"] = item.pop("addr_full", None)  # "Address" is a street + house-number line
            if location.get("IsBranch"):
                item["branch"] = self.clean_branch(item.pop("name"))  # location label, brand stripped
                item["opening_hours"] = self.parse_hours(location.get("WorkTimeFull"))
                apply_category(Categories.BANK, item)
            elif location.get("IsBankomatPumb"):
                item.pop("name", None)  # Title is the bank's legal name, not a location label
                apply_category(Categories.ATM, item)
            elif location.get("IsPTKS"):
                item.pop("name", None)  # Title is a generic "self-service terminal" label
                apply_category({"amenity": "payment_terminal"}, item)
            else:
                continue  # points of sale / agent desks hosted in third-party shops, out of scope
            yield item

    @staticmethod
    def valid_coordinates(location: dict[str, Any]) -> bool:
        try:
            lat, lon = float(location["Lat"]), float(location["Lng"])
        except (KeyError, TypeError, ValueError):
            return False
        return -90 <= lat <= 90 and -180 <= lon <= 180 and (lat or lon)

    @staticmethod
    def clean_branch(title: str | None) -> str | None:
        # Titles are "ВІДДІЛЕННЯ №N ПУМБ [ЕКСПРЕС] В М. <city>"; drop the embedded brand so branch holds
        # the location-specific label only (NSI supplies name=ПУМБ), as DATA_FORMAT expects.
        return re.sub(r"\s+ПУМБ(\s+ЕКСПРЕС)?\s+", " ", title).strip() if title else None

    @staticmethod
    def parse_hours(work_time_full: str | None) -> str | None:
        # WorkTimeFull is "Mon-Fri | Sat | Sun | break | <cashier fields...>". The first three are the
        # branch's own daily hours (a HH:MM-HH:MM range, or "вихідний"/blank when closed/unknown); the
        # trailing cashier/break fields are inconsistent and ignored, so lunch breaks are not captured.
        parts = [part.strip() for part in (work_time_full or "").split("|")]
        if len(parts) < 3:
            return None
        hours = OpeningHours()
        try:
            for days, value in ((DAYS_WEEKDAY, parts[0]), (["Sa"], parts[1]), (["Su"], parts[2])):
                if match := HOURS_RANGE.match(value):
                    hours.add_days_range(days, match.group(1), match.group(2))
        except ValueError:
            return None
        return hours.as_opening_hours() or None
