import json
import re
from typing import AsyncIterator, Iterable

from scrapy import Request, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature


class MrTransmissionUSSpider(Spider):
    name = "mr_transmission_us"
    item_attributes = {"brand": "Mr. Transmission"}
    allowed_domains = ["mrtransmission.com", "milexcompleteautocare.com"]

    primary_url = "https://mrtransmission.com/wp-admin/admin-ajax.php?action=asl_load_stores&load_all=1&layout=1"
    supplemental_url = (
        "https://milexcompleteautocare.com/wp-admin/admin-ajax.php?action=asl_load_stores&load_all=1&layout=1"
    )

    state_corrections = {
        "Illiinois": "Illinois",
        "Illinios": "Illinois",
        "Illionois": "Illinois",
        "MIchigan": "Michigan",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.seen_addresses = set()

    async def start(self) -> AsyncIterator[Request]:
        yield Request(self.primary_url, callback=self.parse_primary)

    def parse_primary(self, response: Response) -> Iterable[Feature | Request]:
        yield from self.parse_locations(response, "mrtransmission")
        yield Request(self.supplemental_url, callback=self.parse_supplemental)

    def parse_supplemental(self, response: Response) -> Iterable[Feature]:
        yield from self.parse_locations(response, "milex")

    def parse_locations(self, response: Response, source: str) -> Iterable[Feature]:
        for location in response.json():
            if location.get("country") != "United States":
                continue

            location["state"] = self.state_corrections.get(location["state"], location["state"])
            address_key = self.normalized_address(location)
            if address_key in self.seen_addresses:
                continue
            self.seen_addresses.add(address_key)

            item = DictParser.parse(location)
            item["ref"] = f"{source}:{location['id']}"
            item["branch"] = item.pop("name")
            item["street_address"] = item.pop("street")
            item["opening_hours"] = self.parse_opening_hours(location.get("open_hours"))

            apply_category(Categories.SHOP_CAR_REPAIR, item)
            yield item

    @staticmethod
    def normalized_address(location: dict) -> str:
        address = "|".join(location.get(key, "") for key in ("street", "city", "state", "postal_code", "country"))
        return re.sub(r"[^a-z0-9]", "", address.lower())

    @staticmethod
    def parse_opening_hours(raw_hours: str | None) -> OpeningHours:
        hours = OpeningHours()
        for day, ranges in json.loads(raw_hours or "{}").items():
            if ranges == "0":
                hours.set_closed(day)
                continue
            if not isinstance(ranges, list):
                continue
            for time_range in ranges:
                open_time, close_time = time_range.split(" - ")
                hours.add_range(day, open_time, close_time, time_format="%I:%M %p")
        return hours
