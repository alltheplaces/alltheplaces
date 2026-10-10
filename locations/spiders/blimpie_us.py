import re
from typing import Any, Iterable

import chompjs
from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.items import Feature

# Blimpie uses the Kahala Brands store locator, which writes every store onto
# the locator page as a series of Locator.stores[n] = {...} JavaScript
# assignments. No opening hours are published.


class BlimpieUSSpider(Spider):
    name = "blimpie_us"
    item_attributes = {"brand": "Blimpie", "brand_wikidata": "Q4926479"}
    allowed_domains = ["www.blimpie.com"]
    start_urls = ["https://www.blimpie.com/stores/"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        for match in re.finditer(r"Locator\.stores\[\d+\]\s*=\s*", response.text):
            location = chompjs.parse_js_object(response.text[match.end() :])

            if location.get("StatusName") == "Coming Soon":
                continue

            item = DictParser.parse(location)
            item["ref"] = location["StoreId"]
            item["name"] = None
            item.pop("addr_full", None)
            item["street_address"] = location["Address"].strip(" ,")
            item["state"] = location.get("State")
            item["branch"] = self.parse_branch(location)

            apply_category(Categories.FAST_FOOD, item)
            item["extras"]["cuisine"] = "sandwich"

            yield item

    @staticmethod
    def parse_branch(location: dict) -> str | None:
        """
        "Name" is a free text field. It usually repeats the street address or
        the city, which is no use as a branch name, but sometimes names the
        mall, campus or shop the store sits inside.
        """
        name = (location.get("Name") or "").strip()
        if not name or any(character.isdigit() for character in name):
            return None

        def normalise(value: str) -> str:
            return re.sub(r"[^a-z]", "", value.lower())

        city, state = location.get("City") or "", location.get("State") or ""
        if normalise(name) in [normalise(city), normalise(city + state), normalise(state)]:
            return None

        return name
