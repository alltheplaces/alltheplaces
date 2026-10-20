import re
from typing import Any, Iterable

import chompjs
from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.items import Feature

# Surf City Squeeze is a Kahala Brands franchise, and its locator page writes
# every store onto the page as a series of Locator.stores[n] = {...} JavaScript
# assignments. Stores that have not opened yet are marked "Coming Soon".
#
# Most stores sit in a mall food court, named either in LocationHelp or in the
# free text Name field, which otherwise just repeats the city and state.
#
# No opening hours are published.
#
# No brand:wikidata is set because the chain has no Wikidata item.


class SurfCitySqueezeUSSpider(Spider):
    name = "surf_city_squeeze_us"
    item_attributes = {"brand": "Surf City Squeeze"}
    allowed_domains = ["www.surfcitysqueeze.com"]
    start_urls = ["https://www.surfcitysqueeze.com/stores/"]

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

            apply_category(Categories.FAST_FOOD, item)
            item["extras"]["cuisine"] = "juice"

            yield item

    @staticmethod
    def branch(location: dict) -> str | None:
        """
        LocationHelp names the mall where there is one, and Name is a label that
        often just repeats the city and state.
        """
        if help_text := (location.get("LocationHelp") or "").strip():
            return help_text

        name = (location.get("Name") or "").strip()
        city = (location.get("City") or "").strip()
        if not name or name.lower().startswith(city.lower()):
            return None
        return name
