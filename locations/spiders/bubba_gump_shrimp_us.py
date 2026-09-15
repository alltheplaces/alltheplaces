import re
from typing import Any, Iterable

import chompjs
from pycountry import subdivisions
from scrapy import Selector, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_EN, OpeningHours
from locations.items import Feature

# Bubba Gump uses a BentoBox store locator, which passes every location to a
# storeLocatorConfig() call on the locator page as a JavaScript object literal.
#
# The locator covers the whole chain, so restaurants in Mexico, Canada, Japan,
# Hong Kong, Indonesia and Australia are dropped by checking the "state" field
# against the US subdivision list.
#
# The "state" field cannot be trusted on its own: the Bali restaurant is
# labelled "ID", which collides with Idaho, and one of the Cancun airport
# restaurants is labelled "TX". Coordinates are checked as well.
#
# Opening hours come from an HTML blob that also carries happy hour promotions
# and dated holiday hours, so those lines are skipped before parsing.

US_SUBDIVISIONS = {subdivision.code.removeprefix("US-") for subdivision in subdivisions.get(country_code="US")}
# Territories have their own ISO country codes and are labelled accordingly.
US_TERRITORIES = {"AS", "GU", "MP", "PR", "UM", "VI"}
# Bounding boxes as (min_lat, max_lat, min_lon, max_lon) for the contiguous
# states, Alaska, Hawaii and Puerto Rico.
US_BOUNDING_BOXES = [
    (24.0, 49.5, -125.0, -66.5),
    (51.0, 72.0, -180.0, -129.0),
    (18.5, 22.5, -161.0, -154.5),
    (17.8, 18.6, -67.5, -65.2),
]


class BubbaGumpShrimpUSSpider(Spider):
    name = "bubba_gump_shrimp_us"
    item_attributes = {"brand": "Bubba Gump Shrimp Co.", "brand_wikidata": "Q50024"}
    allowed_domains = ["www.bubbagump.com"]
    start_urls = ["https://www.bubbagump.com/store-locator/"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        config = chompjs.parse_js_object(response.text.split("storeLocatorConfig(", 1)[1])

        for location in config["locations"]:
            state = (location.get("state") or "").strip().upper()
            if state not in US_SUBDIVISIONS or not self.in_the_us(location):
                continue

            item = DictParser.parse(location)
            item["ref"] = location["slug"]
            item["country"] = state if state in US_TERRITORIES else "US"
            item["branch"] = location["name"]
            item["name"] = None
            # DictParser also picks up the preformatted "address" string and
            # the street on their own; street_address alone is enough.
            item.pop("addr_full", None)
            item["street"] = None
            item["street_address"] = location.get("street")
            item["phone"] = location.get("phone_number")
            item["website"] = response.urljoin(location["url"])

            item["opening_hours"] = self.parse_opening_hours(location)

            apply_category(Categories.RESTAURANT, item)
            item["extras"]["cuisine"] = "seafood"

            yield item

    @staticmethod
    def in_the_us(location: dict) -> bool:
        try:
            lat, lon = float(location["lat"]), float(location["lng"])
        except (KeyError, TypeError, ValueError):
            return False
        return any(
            min_lat <= lat <= max_lat and min_lon <= lon <= max_lon
            for min_lat, max_lat, min_lon, max_lon in US_BOUNDING_BOXES
        )

    @staticmethod
    def parse_opening_hours(location: dict) -> OpeningHours:
        oh = OpeningHours()

        if any((structured_hours := location.get("structured_hours") or {}).values()):
            for day, periods in structured_hours.items():
                for period in periods:
                    oh.add_range(day.title()[:2], period["open_time"][:5], period["close_time"][:5])
            return oh

        lines = [line.strip() for line in Selector(text=location.get("hours") or "").xpath("//text()").getall()]
        lines = [
            line
            for line in lines
            # Drops happy hour promotions, the "Holiday Hours" heading, and the
            # dated holiday times beneath it.
            if line and "hour" not in line.lower() and not re.search(r"\b(19|20)\d{2}\b", line)
        ]
        oh.add_ranges_from_string(" ".join(lines), days=DAYS_EN)
        return oh
