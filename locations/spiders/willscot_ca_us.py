import json
import re
from typing import Any, AsyncIterator
from urllib.parse import urljoin

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class WillscotCAUSSpider(Spider):
    name = "willscot_ca_us"
    item_attributes = {"brand": "WillScot", "brand_wikidata": "Q123415387"}
    allowed_domains = ["www.willscot.com"]
    STATE_SUFFIX_RE = re.compile(r"\s[A-Z]{2}$")

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(
            url="https://www.willscot.com/webruntime/api/apex/execute?asGuest=true&htmlEncode=false",
            data={
                "namespace": "",
                "classname": "@udd/01pPa00000DbbKV",
                "method": "getAllBranches",
                "isContinuation": False,
                "cacheable": False,
            },
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        data = json.loads(response.json()["returnValue"])

        location_fields_map = {}

        for results in DictParser.iter_matching_keys(data["includes"], "Entry"):
            for location in results:
                fields = location.get("fields", {})

                if "cardTexts" in fields:  # location details with address, opening hours etc
                    # Normalize internalLabel into a slug-like key for matching locations.
                    # Usually aligns with slug, but may require partial match in some cases.
                    key = fields["internalLabel"].lower().split("-")[0].strip().replace(" ", "-")

                    location_fields_map[key] = fields["cardTexts"]

        for location in data["items"]:
            location.update(location.pop("fields"))
            slug = location["slug"]
            item = DictParser.parse(location)
            item["branch"] = self.STATE_SUFFIX_RE.sub(
                "",
                item.pop("name"),
            )
            item["website"] = urljoin(
                "https://www.willscot.com/locations/details/",
                slug,
            )

            for key, value in location_fields_map.items():
                if slug in key:
                    item["opening_hours"] = self.parse_opening_hours(value)
                    item["addr_full"] = self.parse_address(value)
                    break

            apply_category(Categories.SHOP_RENTAL, item)

            yield item

    def parse_opening_hours(self, location_details: list[dict]) -> OpeningHours:
        opening_hours = OpeningHours()
        for info in location_details:
            if info["key"] in {"Hours", "Opening Hours"}:
                opening_hours.add_ranges_from_string(info["value"].replace("\\n", " "))
                break
        return opening_hours

    def parse_address(self, location_details: list[dict]) -> str:
        for info in location_details:
            if info["key"] == "Address":
                return info["value"]

        return ""
