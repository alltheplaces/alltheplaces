import re
from typing import Any, Iterable

import chompjs
from scrapy import Selector, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_EN, OpeningHours
from locations.items import Feature

# Chart House uses a BentoBox store locator, which passes every location to a
# storeLocatorConfig() call on the locator page as a JavaScript object literal.
#
# Opening hours come from an HTML blob that also carries happy hour promotions
# and dated holiday hours, so those lines are skipped before parsing to stop
# them being read as extra opening periods.
#
# No brand:wikidata is set: Wikidata has no item for the chain, only one for a
# single restaurant of that name.


class ChartHouseUSSpider(Spider):
    name = "chart_house_us"
    item_attributes = {"brand": "Chart House"}
    allowed_domains = ["www.chart-house.com"]
    start_urls = ["https://www.chart-house.com/store-locator/"]

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
            item["extras"]["cuisine"] = "seafood"

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
