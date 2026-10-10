import re
from typing import Any, Iterable

import chompjs
from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.items import Feature

# Pinkberry is a Kahala Brands franchise, and its locator page writes every
# shop onto the page as a series of Locator.stores[n] = {...} JavaScript
# assignments. Shops that have not opened yet are marked "Coming Soon".
#
# The Name field is a free text label — sometimes the city and state, sometimes
# the mall or airport terminal — so it is only kept as the branch when it adds
# something the address does not.
#
# No opening hours are published.


class PinkberryUSSpider(Spider):
    name = "pinkberry_us"
    item_attributes = {"brand": "Pinkberry", "brand_wikidata": "Q2904053"}
    allowed_domains = ["www.pinkberry.com"]
    start_urls = ["https://www.pinkberry.com/stores/"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        for match in re.finditer(r"Locator\.stores\[\d+\]\s*=\s*", response.text):
            location = chompjs.parse_js_object(response.text[match.end() :])

            if location.get("StatusName") == "Coming Soon":
                continue

            item = DictParser.parse(location)
            item["ref"] = location["StoreId"]
            item["name"] = None
            # DictParser also picks the street up as the joined address.
            item.pop("addr_full", None)
            item["street_address"] = (location.get("Address") or "").strip(" ,")
            item["state"] = location.get("State")
            item["branch"] = self.branch(location)

            apply_category(Categories.ICE_CREAM, item)
            item["extras"]["cuisine"] = "frozen_yogurt"

            yield item

    @staticmethod
    def branch(location: dict) -> str | None:
        """
        LocationHelp names the mall or terminal where there is one, and Name is
        a label that often just repeats the city and state.
        """
        if help_text := (location.get("LocationHelp") or "").strip():
            return help_text

        name = (location.get("Name") or "").strip()
        city = (location.get("City") or "").strip()
        if not name or name.lower().startswith(city.lower()):
            return None
        return name
