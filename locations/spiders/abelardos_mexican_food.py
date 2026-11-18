import json
import re
from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature

# Every restaurant the chain has is listed on this one page, which is built by
# script from data the site ships inside it.
LOCATIONS = "https://www.abelardosmexicanfood.com/locations"
WARMUP = re.compile(r'<script[^>]*id="wix-warmup-data"[^>]*>(.*?)</script>', re.S)
# "Bellevue, NE"
CITY_AND_STATE = re.compile(r"^(?P<city>.+?),\s*(?P<state>[A-Za-z]{2})\.?\s*$")


class AbelardosMexicanFoodSpider(Spider):
    """The chain keeps its restaurants in a handful of tables, one per state.

    What it publishes of a restaurant is its address and its telephone number.
    There are no coordinates - two of the sixty nine carry any - no opening
    hours and no name beyond the town, so that is all this spider can state.

    The addresses are written by hand and show it: some are a tidy
    "4005 Twin Creek Dr, Bellevue, NE 68123", others separate their parts with
    tabs or a newline, run the town straight on after the street, or stop before
    the postcode altogether. The town is therefore taken from the field that
    states it on its own, and the street is whatever the address says before it.
    """

    name = "abelardos_mexican_food"
    # Neither the chain nor any of its restaurants has a Wikidata item.
    item_attributes = {"brand": "Abelardo's Mexican Food"}
    allowed_domains = ["www.abelardosmexicanfood.com"]
    start_urls = [LOCATIONS]
    # The site turns a caller away with a holding page now and again, and
    # everything the spider wants is behind this single request.
    custom_settings = {"RETRY_TIMES": 5}

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        for record in self.records(response):
            address = self.stated_address(record)
            city, state = self.town(record)

            item = Feature()
            item["ref"] = record.get("_id")
            item["street_address"] = self.street(address, city)
            item["city"] = city
            item["state"] = state
            item["postcode"] = self.postcode(record, address, state)
            item["country"] = "US"
            item["phone"] = record.get("phoneNumber")

            # Two restaurants, and only two, state where they are.
            if isinstance(point := self.point(record), dict):
                item["lat"] = point.get("latitude")
                item["lon"] = point.get("longitude")

            apply_category(Categories.FAST_FOOD, item)
            item["extras"]["cuisine"] = "mexican"
            yield item

    def records(self, response: Response) -> Iterable[dict]:
        if not (found := WARMUP.search(response.text)):
            self.logger.error(f"No data found on {response.url}")
            return
        try:
            warmup = json.loads(found.group(1))
        except ValueError:
            self.logger.error(f"Unreadable data on {response.url}")
            return
        tables = (
            warmup.get("appsWarmupData", {}).get("dataBinding", {}).get("dataStore", {}).get("recordsByCollectionId")
        )
        if not isinstance(tables, dict):
            self.logger.error(f"No tables of restaurants on {response.url}")
            return
        for table in tables.values():
            if not isinstance(table, dict):
                continue
            for record in table.values():
                if isinstance(record, dict) and record.get("_id"):
                    yield record

    @staticmethod
    def stated_address(record: dict) -> str:
        """Return the address as one line, however the record happens to hold it."""
        address = record.get("address")
        if isinstance(address, dict):
            address = address.get("formatted") or ""
        return re.sub(r"\s+", " ", address if isinstance(address, str) else "").strip()

    def town(self, record: dict) -> tuple[str | None, str | None]:
        state = record.get("state")
        if match := CITY_AND_STATE.match(re.sub(r"\s+", " ", record.get("cityAndState") or "").strip()):
            return match["city"], (state or match["state"]).upper()
        return None, (state or "").upper() or None

    @staticmethod
    def street(address: str, city: str | None) -> str | None:
        """Return what an address says before it reaches the town.

        A full stop comes and goes between the records, as in "St Joseph" for
        "St. Joseph", so it is treated as optional on either side.
        """
        if not address:
            return None
        if city:
            town = re.escape(city).replace(r"\.", ".?").replace(r"\ ", r"\s+")
            if found := re.search(rf",?\s*{town}\b", address, re.IGNORECASE):
                if street := address[: found.start()].strip(" ,"):
                    return street
        # Failing that, take off a trailing state, postcode and country.
        return re.sub(r",?\s*[A-Za-z]{2},?\s*\d{5}(?:-\d{4})?,?\s*(?:USA)?\.?$", "", address).strip(" ,") or None

    @staticmethod
    def postcode(record: dict, address: str, state: str | None) -> str | None:
        address_object = record.get("address")
        if isinstance(address_object, dict) and (stated := address_object.get("postalCode")):
            return stated
        # A street number can be five figures long too, so the postcode is only
        # read where it follows the state.
        if state and (found := re.search(rf"\b{state}\b[,\s]+(\d{{5}}(?:-\d{{4}})?)", address, re.IGNORECASE)):
            return found.group(1)
        return None

    @staticmethod
    def point(record: dict) -> dict | None:
        address = record.get("address")
        if isinstance(address, dict) and isinstance(location := address.get("location"), dict):
            if location.get("latitude") is not None:
                return location
        return None
