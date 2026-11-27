import re
from typing import Any, Iterable

import chompjs
from scrapy import Request, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature

# Honeygrow uses a BentoBox store locator, which passes every location to a
# storeLocatorConfig() call on the locator page as a JavaScript object literal.
#
# The hours in that object are only a static fallback. The site hydrates the
# real hours from cdn.honeygrow.com/hours.json, keyed by the store number
# each location's hours blob carries in its data-hg-store attribute, so the
# hours are taken from that file instead.


class HoneygrowUSSpider(Spider):
    name = "honeygrow_us"
    item_attributes = {"brand": "Honeygrow", "brand_wikidata": "Q140091870"}
    allowed_domains = ["www.honeygrow.com", "cdn.honeygrow.com"]
    start_urls = ["https://www.honeygrow.com/hours-and-locations/"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Request]:
        config = chompjs.parse_js_object(response.text.split("storeLocatorConfig(", 1)[1])
        yield Request(
            url="https://cdn.honeygrow.com/hours.json",
            callback=self.parse_locations,
            cb_kwargs={"locations": config["locations"]},
        )

    def parse_locations(self, response: Response, locations: list[dict]) -> Iterable[Feature]:
        hours_by_store = response.json()["locations"]

        for location in locations:
            item = DictParser.parse(location)
            item["ref"] = location["slug"]
            item["branch"] = location["name"]
            item["name"] = None
            # DictParser also picks up the preformatted "address" string and
            # the street on their own; street_address alone is enough.
            item.pop("addr_full", None)
            item["street"] = None
            item["street_address"] = location["street"]
            item["phone"] = location["phone_number"]
            item["website"] = "https://www.honeygrow.com" + location["url"]

            item["opening_hours"] = self.parse_opening_hours(location, hours_by_store)

            apply_category(Categories.FAST_FOOD, item)

            yield item

    @staticmethod
    def parse_opening_hours(location: dict, hours_by_store: dict) -> OpeningHours:
        oh = OpeningHours()
        store_number = re.search(r'data-hg-store="(\d+)"', location["hours"]).group(1)
        for rule in hours_by_store[store_number]["openingHours"]:
            oh.add_range(rule["day"][:2], rule["opens"], rule["closes"], time_format="%H:%M")
        return oh
