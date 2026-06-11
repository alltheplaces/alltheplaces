import re
from typing import AsyncIterator
from urllib.parse import urljoin

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import CLOSED_NO, DAYS_NO, OpeningHours, sanitise_day


class ClasOhlsonNOSpider(Spider):
    name = "clas_ohlson_no"
    item_attributes = {"brand": "Clas Ohlson", "brand_wikidata": "Q3356220"}
    allowed_domains = ["www.clasohlson.com"]
    custom_settings = {"USER_AGENT": ""}
    postcode_city_pattern = re.compile(r"^(\d{4})\s+(.+)$")

    def _make_request(self, page: int) -> JsonRequest:
        return JsonRequest(
            url=(
                "https://www.clasohlson.com/no/store-finder"
                "?q=Norge&latitude=60.47202399999999&longitude=8.468945999999999&page={}".format(page)
            ),
            meta={"page": page},
        )

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield self._make_request(0)

    @staticmethod
    def _parse_address(address_html: str, branch: str | None) -> tuple[str | None, str | None, str | None]:
        if not address_html:
            return (None, None, None)

        lines = [line.strip() for line in address_html.split("<br />") if line and line.strip()]
        postcode = city = None
        postcode_line_index = None

        for index, line in enumerate(lines):
            if match := ClasOhlsonNOSpider.postcode_city_pattern.match(line):
                postcode, city = match.group(1), match.group(2).strip()
                postcode_line_index = index
                break

        street_candidates = [
            line
            for line in (lines[:postcode_line_index] if postcode_line_index is not None else lines)
            if "clas ohlson" not in line.lower()
        ]

        if branch:
            branch_lower = branch.lower()
            street_candidates = [line for line in street_candidates if line.lower() != branch_lower]

        street_address = next(
            (line for line in reversed(street_candidates) if any(char.isdigit() for char in line)),
            street_candidates[-1] if street_candidates else None,
        )

        return (street_address, postcode, city)

    @staticmethod
    def _parse_opening_hours(store_timings: dict) -> OpeningHours:
        oh = OpeningHours()
        for day, times in store_timings.items():
            day_en = sanitise_day(day, DAYS_NO)
            if times.lower() in CLOSED_NO:
                oh.set_closed(day_en)
            else:
                oh.add_range(day_en, *times.split(" - "))

        return oh

    def parse(self, response: Response):
        try:
            response_data = response.json()
        except ValueError:
            self.logger.warning("Skipping non-JSON response from %s", response.url)
            return
        stores = response_data.get("data", [])
        total = response_data.get("total", 0)

        for store in stores:
            item = DictParser.parse(store)
            store_addresses = store.get("storeAddresses", {})
            branch = store_addresses.get("SalesChannelName")
            address_html = store.get("storeAddresses", {}).get("SalesChannelAddress")
            street_address, postcode, city = self._parse_address(address_html, branch)
            store_map_icon = store.get("storeMapIcon")

            if branch == "Kundesenteret":
                continue

            item.update(
                {
                    "ref": store_addresses.get("SalesChannelAddressId"),
                    "name": self.item_attributes["brand"],
                    "branch": branch,
                    "street_address": street_address,
                    "postcode": postcode,
                    "city": city,
                    "country": "NO",
                    "phone": store.get("storeContact"),
                    "website": None,
                    "image": urljoin("https://www.clasohlson.com", store_map_icon) if store_map_icon else None,
                }
            )
            try:
                item["opening_hours"] = self._parse_opening_hours(store.get("storeTimings", {}))
            except Exception:
                self.logger.error("Error parsing opening hours")

            apply_category(Categories.SHOP_HARDWARE, item)
            yield item

        page = response.meta["page"]
        if (page + 1) * 10 < total:
            yield self._make_request(page + 1)
