import re
from copy import deepcopy
from typing import Any, Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.spiders.toyota_au import TOYOTA_SHARED_ATTRIBUTES


class ToyotaUSSpider(SitemapSpider, JSONBlobSpider):
    name = "toyota_us"
    item_attributes = TOYOTA_SHARED_ATTRIBUTES
    sitemap_urls = ["https://www.toyota.com/sitemap-dealers.xml"]
    locations_key = "dealers"
    zipcode_match = re.compile(r"/dealers/[-\w]+/[-\w]+/(\d+)/[-\w]+/?$")
    custom_settings = {"ROBOTSTXT_OBEY": False, "DEFAULT_REQUEST_HEADERS": {"origin": "https://www.toyota.com"}}

    def sitemap_filter(self, entries: Iterable[dict[str, Any]]) -> Iterable[dict[str, Any]]:
        for entry in entries:
            if match := re.search(self.zipcode_match, entry["loc"]):
                """
                Dealer location sitemap URLs do not provide coordinates; therefore, API is used.
                The resultsMax=1 parameter limits each request to a single location, preventing duplicate results.
                """
                yield {
                    "loc": f"https://dealers.prod.webservices.toyota.com/v1/dealers?resultsMax=1&zipcode={match.group(1)}"
                }

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        feature.pop("region", None)
        item["ref"] = feature["dealerId"]

        # All locations appear to offer both sales and service.
        yield self.build_shop(item, feature)
        yield self.build_service(item, feature)

        if feature.get("hoursParts"):
            yield self.build_parts(item, feature)

    def build_shop(self, item: Feature, feature: dict) -> Feature:
        shop_item = deepcopy(item)
        shop_item["ref"] = f"{item['ref']}-SHOP"
        shop_item["opening_hours"] = self.parse_opening_hours(feature, "sales")
        apply_category(Categories.SHOP_CAR, shop_item)
        return shop_item

    def build_service(self, item: Feature, feature: dict) -> Feature:
        service_item = deepcopy(item)
        service_item["ref"] = f"{item['ref']}-SERVICE"
        service_item["phone"] = feature.get("phoneNumberService")
        service_item["opening_hours"] = self.parse_opening_hours(feature, "service")
        apply_category(Categories.SHOP_CAR_REPAIR, service_item)
        return service_item

    def build_parts(self, item: Feature, feature: dict) -> Feature:
        parts_item = deepcopy(item)
        parts_item["ref"] = f"{item['ref']}-PARTS"
        parts_item["phone"] = feature.get("phoneNumberParts")
        parts_item["opening_hours"] = self.parse_opening_hours(feature, "parts")
        apply_category(Categories.SHOP_CAR_PARTS, parts_item)
        return parts_item

    def parse_opening_hours(self, feature: dict, location_type: str) -> OpeningHours:
        if location_type == "sales":
            hours_list = feature.get("sales", {}).get("hours", []) or feature.get("general", {}).get("hours", [])
        else:
            hours_list = feature.get(location_type, {}).get("hours", [])

        opening_hours = OpeningHours()
        for index, rule in enumerate(hours_list):
            day = DAYS[index - 1]
            if "Closed" in rule:
                opening_hours.set_closed(day)
                continue
            for shift in rule:
                open_time, close_time = shift.split(",")
                opening_hours.add_range(day, open_time.strip(), close_time.strip(), "%H%M")
        return opening_hours
