import json
import re
from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS, DAYS_EN, OpeningHours
from locations.items import Feature

# The locations page carries the restaurants twice, and neither list is
# complete on its own:
#
#   * the Next.js page data has coordinates and a per day hours array, but only
#     covers the restaurants in the store locator widget, and
#   * the schema.org Organization block lists every restaurant, including ones
#     the widget omits, but has no coordinates.
#
# Both are read, keyed on the store code, so the widget data is used where it
# exists and the structured data fills in the rest.
#
# No brand:wikidata is set because the chain has no Wikidata item.


class HelloBistroUSSpider(Spider):
    name = "hello_bistro_us"
    item_attributes = {"brand": "Hello Bistro"}
    allowed_domains = ["hellobistro.com"]
    start_urls = ["https://hellobistro.com/locations"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        seen = set()

        for location in self.page_data(response):
            seen.add(str(location["storeCode"]))
            yield self.parse_widget_location(location)

        for location in self.structured_data(response):
            if not (store_code := re.search(r"HBUS-(\d+)", location.get("url") or "")):
                continue
            if store_code.group(1) in seen:
                continue
            yield self.parse_structured_location(location, store_code.group(1))

    @staticmethod
    def page_data(response: Response) -> list[dict]:
        if not (data := response.xpath('//script[@id="__NEXT_DATA__"]/text()').get()):
            return []
        return json.loads(data).get("props", {}).get("pageProps", {}).get("locations") or []

    @staticmethod
    def structured_data(response: Response) -> list[dict]:
        for block in response.xpath('//script[@type="application/ld+json"]/text()').getall():
            data = json.loads(block)
            if data.get("@type") == "Organization":
                return data.get("subOrganization") or []
        return []

    def parse_widget_location(self, location: dict) -> Feature:
        item = Feature()
        item["ref"] = str(location["storeCode"])
        item["branch"] = location.get("city")
        item["street_address"] = ", ".join(location.get("addressLines") or [])
        item["city"] = location.get("city")
        item["state"] = location.get("state")
        item["postcode"] = location.get("postalCode")
        item["country"] = location.get("country")
        item["lat"] = location.get("latitude")
        item["lon"] = location.get("longitude")
        item["phone"] = (location.get("phoneNumbers") or [None])[0]
        item["website"] = re.sub(r"(?<!:)//", "/", location.get("websiteURL") or "") or None

        oh = OpeningHours()
        # One [open, close] pair per day, starting on Monday.
        for day, hours in zip(DAYS, location.get("businessHours") or []):
            if len(hours) == 2:
                oh.add_range(day, hours[0], hours[1])
        item["opening_hours"] = oh

        self.apply_attributes(item)
        return item

    def parse_structured_location(self, location: dict, store_code: str) -> Feature:
        address = location.get("address") or {}

        item = Feature()
        item["ref"] = store_code
        item["branch"] = (location.get("name") or "").split("\u2013")[-1].strip()
        item["street_address"] = address.get("streetAddress")
        item["city"] = address.get("addressLocality")
        item["state"] = address.get("addressRegion")
        item["postcode"] = address.get("postalCode")
        item["country"] = address.get("addressCountry")
        item["phone"] = location.get("telephone")

        oh = OpeningHours()
        for rule in location.get("openingHoursSpecification") or []:
            for day in rule.get("dayOfWeek") or []:
                oh.add_range(DAYS_EN[day], rule["opens"], rule["closes"])
        item["opening_hours"] = oh

        self.apply_attributes(item)
        return item

    @staticmethod
    def apply_attributes(item: Feature) -> None:
        apply_category(Categories.FAST_FOOD, item)
        item["extras"]["cuisine"] = "salad;burger"
