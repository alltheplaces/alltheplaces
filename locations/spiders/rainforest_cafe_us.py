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

# Rainforest Cafe uses a BentoBox store locator, which passes every location to
# a storeLocatorConfig() call on the locator page as a JavaScript object
# literal.
#
# The locator covers the whole chain, so the restaurants in France, Japan,
# Malta and Canada are dropped. The "state" field is not enough on its own: the
# Canadian restaurant, in Niagara Falls Ontario, is labelled "AZ" and sits close
# enough to the border to pass a bounding box check, so a US postcode is
# required as well.
#
# Opening hours come from an HTML blob that also carries happy hour promotions
# and dated holiday hours, so those lines are skipped before parsing.

US_SUBDIVISIONS = {subdivision.code.removeprefix("US-") for subdivision in subdivisions.get(country_code="US")}


class RainforestCafeUSSpider(Spider):
    name = "rainforest_cafe_us"
    item_attributes = {"brand": "Rainforest Cafe", "brand_wikidata": "Q3391111"}
    allowed_domains = ["www.rainforestcafe.com"]
    start_urls = ["https://www.rainforestcafe.com/store-locator/"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        config = chompjs.parse_js_object(response.text.split("storeLocatorConfig(", 1)[1])

        for location in config["locations"]:
            if (location.get("state") or "").strip().upper() not in US_SUBDIVISIONS:
                continue
            if not re.fullmatch(r"\d{5}(-\d{4})?", (location.get("postal_code") or "").strip()):
                continue

            item = DictParser.parse(location)
            item["ref"] = location["slug"]
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

            yield item

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
