import json
import re
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_EN, OpeningHours
from locations.items import Feature


class CsobSKSpider(Spider):
    name = "csob_sk"
    item_attributes = {"brand": "ČSOB", "brand_wikidata": "Q340135"}
    start_urls = ["https://www.csob.sk/o/branch-rest/branches?lang=sk"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in json.loads(response.body.decode("utf-8")).get("features", []):
            location_type = location.get("properties", {}).get("type")
            item = self.parse_location(location)

            if location_type == 1:  # Pobočka ČSOB Banky
                apply_category(Categories.BANK, item)
            elif location_type == 2:  # Bankomat
                apply_category(Categories.ATM, item)
            else:
                if location_type not in (3, 5):
                    self.logger.error("Unexpected location type: {}".format(location_type))
                continue

            yield item

    def parse_location(self, location: dict[str, Any]) -> Feature:
        item = DictParser.parse(location)
        properties = location.get("properties", {})
        address = properties.get("address", {})

        item["street_address"] = address.get("street")
        item["city"] = address.get("city")
        item["postcode"] = address.get("postCode")
        item["phone"] = None
        item["email"] = None

        if branch := self.clean_branch(address.get("locationDescr")):
            item["branch"] = branch

        if opening_hours := self.parse_opening_hours(properties.get("open", {}).get("days")):
            item["opening_hours"] = opening_hours

        return item

    @staticmethod
    def clean_branch(raw_branch: str | None) -> str | None:
        if not raw_branch:
            return None

        branch = raw_branch.strip()
        if match := re.fullmatch(r"Pobočka\s+ČSOB\s*\((.+)\)", branch, flags=re.IGNORECASE):
            branch = match.group(1)
        else:
            branch = re.sub(r"^Pobočka\s+ČSOB\s*", "", branch, flags=re.IGNORECASE).strip()
            branch = branch.removeprefix("(").removesuffix(")").strip()

        if branch in {"ČSOB", "Pobočka", "Pobočka ČSOB"}:
            return None
        return branch or None

    @staticmethod
    def parse_opening_hours(days: dict[str, Any] | None) -> str | None:
        if not days:
            return None

        try:
            oh = OpeningHours()
            for day_name in (
                "MONDAY",
                "TUESDAY",
                "WEDNESDAY",
                "THURSDAY",
                "FRIDAY",
                "SATURDAY",
                "SUNDAY",
            ):
                for section in days.get(day_name, {}).get("sections") or []:
                    start_time = CsobSKSpider.normalise_time(section.get("from"))
                    end_time = CsobSKSpider.normalise_time(section.get("to"), end=True)
                    if start_time and end_time:
                        oh.add_range(DAYS_EN[day_name.title()], start_time, end_time)
            return oh.as_opening_hours() or None
        except (AttributeError, KeyError, TypeError, ValueError):
            return None

    @staticmethod
    def normalise_time(time: str | None, end: bool = False) -> str | None:
        if not time:
            return None
        if end and time == "23:59":
            return "24:00"
        return re.sub(r"^(\d):(\d{2})$", r"0\1:\2", time)
