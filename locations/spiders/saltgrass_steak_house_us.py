from typing import Any, Iterable

import chompjs
from scrapy import Selector, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_EN, OpeningHours
from locations.items import Feature

# Saltgrass Steak House uses a BentoBox store locator. The locator page passes
# every location to a storeLocatorConfig() call as a JavaScript object literal.
#
# Opening hours are published two ways: a structured_hours object that only a
# handful of locations fill in, and an HTML blob that the rest use. The HTML
# also carries happy hour times and ordering links, so lines mentioning happy
# hour are dropped before parsing to stop them being read as a second opening
# period.


class SaltgrassSteakHouseUSSpider(Spider):
    name = "saltgrass_steak_house_us"
    item_attributes = {"brand": "Saltgrass Steak House", "brand_wikidata": "Q7406113"}
    allowed_domains = ["www.saltgrass.com"]
    start_urls = ["https://www.saltgrass.com/store-locator/"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        config = chompjs.parse_js_object(response.text.split("storeLocatorConfig(", 1)[1])

        for location in config["locations"]:
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
        lines = [line for line in lines if line and "happy hour" not in line.lower()]
        oh.add_ranges_from_string(" ".join(lines), days=DAYS_EN)
        return oh
