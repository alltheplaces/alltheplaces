from typing import Any, Iterable

import chompjs
from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature

# Islands uses a BentoBox store locator, which passes every restaurant to a
# storeLocatorConfig() call on the locator page as a JavaScript object literal.
#
# Unlike the other BentoBox sites in this project, this one fills in
# structured_hours, so the hours need no text parsing.


class IslandsRestaurantsUSSpider(Spider):
    name = "islands_restaurants_us"
    item_attributes = {"brand": "Islands", "brand_wikidata": "Q6083699"}
    allowed_domains = ["www.islandsrestaurants.com"]
    start_urls = ["https://www.islandsrestaurants.com/locations/"]

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

            item["opening_hours"] = self.parse_opening_hours(location.get("structured_hours") or {})

            apply_category(Categories.RESTAURANT, item)
            item["extras"]["cuisine"] = "burger"

            yield item

    @staticmethod
    def parse_opening_hours(structured_hours: dict) -> OpeningHours | None:
        """Each day holds a list of {"open_time": "11:00:00", "close_time": "21:00:00"}."""
        oh = OpeningHours()

        for day, periods in structured_hours.items():
            for period in periods or []:
                if (opens := period.get("open_time")) and (closes := period.get("close_time")):
                    oh.add_range(day.title()[:2], opens[:5], closes[:5])

        return oh if oh else None
