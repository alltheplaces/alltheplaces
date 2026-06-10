import re
from typing import AsyncIterator
from urllib.parse import urljoin

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import CLOSED_NO, DAYS_NO, OpeningHours


class ClasOhlsonNOSpider(Spider):
    name = "clas_ohlson_no"
    item_attributes = {"brand": "Clas Ohlson"}
    allowed_domains = ["www.clasohlson.com"]
    custom_settings = {
        "USER_AGENT": "",
    }
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
        hours_string = " ".join(f"{day_name}: {value}" for day_name, value in (store_timings or {}).items() if value)
        if hours_string:
            oh.add_ranges_from_string(hours_string, days=DAYS_NO, closed=CLOSED_NO)

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
                    "opening_hours": self._parse_opening_hours(store.get("storeTimings", {})),
                }
            )

            apply_category(Categories.SHOP_HARDWARE, item)
            yield item

        page = response.meta["page"]
        page_size = len(stores)
        if page_size > 0 and (page + 1) * page_size < total:
            yield self._make_request(page + 1)
