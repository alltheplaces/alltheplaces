import re
from typing import Any, AsyncIterator
from urllib.parse import urlparse

import xmltodict
from scrapy import Spider
from scrapy.http import Request, Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.items import Feature


class SwedbankEELTLVSpider(Spider):
    name = "swedbank_ee_lt_lv"
    item_attributes = {"brand": "Swedbank", "brand_wikidata": "Q1145493"}

    async def start(self) -> AsyncIterator[Any]:
        for cc in ("ee", "lt", "lv"):
            yield Request(url=f"https://www.swedbank.{cc}/finder.xml")

    def parse(self, response: Response, **kwargs: Any) -> Any:
        country = (urlparse(response.url).hostname or "").rsplit(".", 1)[-1].upper()
        for location in xmltodict.parse(response.text)["items"]["item"]:
            if not self.has_coordinates(location):
                continue

            item = self.parse_location(location, country)
            location_type = location.get("type")

            if location_type == "ATM":
                apply_category(Categories.ATM, item)
            elif location_type == "R":
                apply_category(Categories.ATM, item)
                apply_yes_no(Extras.CASH_IN, item, True)
            elif location_type == "branch":
                apply_category(Categories.BANK, item)
            else:
                self.logger.error("Unexpected type: {}".format(location_type))
                continue

            yield item

    def parse_location(self, location: dict[str, Any], country: str) -> Feature:
        item = DictParser.parse(location)

        item["ref"] = "{}-{}".format(country, location["id"])
        item["country"] = country
        item["branch"] = item.pop("name", None)

        if address := item.pop("addr_full", None):
            self.parse_address(item, country, address, "city" in location)

        return item

    def parse_address(self, item: Feature, country: str, address: str, has_city: bool) -> None:
        if has_city:
            item["street_address"] = address
            return

        if country == "EE" and (
            match := re.match(r"(?P<street_address>.+),\s*(?:(?P<postcode>\d{5})\s+)?(?P<city>[^.]+)", address)
        ):
            item["street_address"] = match.group("street_address")
            item["postcode"] = match.group("postcode")
            item["city"] = match.group("city").removesuffix(" Eesti").strip()
        elif country == "LT" and "," in address:
            item["street_address"], item["city"] = [part.strip() for part in address.rsplit(",", 1)]
        elif country == "LV" and "," in address:
            item["city"], item["street_address"] = [part.strip().strip(",") for part in address.split(",", 1)]
        else:
            item["addr_full"] = address

    @staticmethod
    def has_coordinates(location: dict[str, Any]) -> bool:
        return location.get("latitude") not in (None, "null", "0.0") and location.get("longitude") not in (
            None,
            "null",
            "0.0",
        )
