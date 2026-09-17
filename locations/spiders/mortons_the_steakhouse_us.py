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

# Morton's uses a BentoBox store locator, which passes every location to a
# storeLocatorConfig() call on the locator page as a JavaScript object literal.
#
# The locator covers the whole chain, so restaurants in Canada and across Asia
# are dropped. Their "state" field holds a region name rather than a US state
# code, which is what the filter below keys off.
#
# Opening hours come from an HTML blob which also carries promotional "power
# hour" times and dated holiday hours, both of which are skipped so they are
# not read as extra opening periods.

US_SUBDIVISIONS = {subdivision.code.removeprefix("US-") for subdivision in subdivisions.get(country_code="US")}
# Territories have their own ISO country codes and are labelled accordingly.
US_TERRITORIES = {"AS", "GU", "MP", "PR", "UM", "VI"}


class MortonsTheSteakhouseUSSpider(Spider):
    name = "mortons_the_steakhouse_us"
    item_attributes = {"brand": "Morton's The Steakhouse", "brand_wikidata": "Q17022759"}
    allowed_domains = ["www.mortons.com"]
    start_urls = ["https://www.mortons.com/store-locator/"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        config = chompjs.parse_js_object(response.text.split("storeLocatorConfig(", 1)[1])

        for location in config["locations"]:
            state = (location.get("state") or "").strip().upper()
            if state not in US_SUBDIVISIONS:
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
            item["extras"]["cuisine"] = "steak_house"

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
            # Drops "Power Hour" and "Happy Hour" promotions, the "Holiday
            # Hours" heading, and the dated holiday times beneath it.
            if line and "hour" not in line.lower() and not re.search(r"\b(19|20)\d{2}\b", line)
        ]
        oh.add_ranges_from_string(" ".join(lines), days=DAYS_EN)
        return oh
