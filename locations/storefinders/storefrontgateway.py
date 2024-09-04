from typing import Iterable

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address
from locations.automatic_spider_generator import AutomaticSpiderGenerator, DetectionRequestRule, DetectionResponseRule


class StorefrontgatewaySpider(Spider, AutomaticSpiderGenerator):
    """
    A relatively unknown storefinder, associated with https://mi9retail.com/

    To use, specify `start_urls`
    """

    start_urls = []
    api_key: str = ""
    detection_rules = [
        DetectionRequestRule(url=r"^https?:\/\/storefrontgateway\.[w\.-]+/api/stores"),
        DetectionResponseRule(js_objects={"start_urls": r"[window.__PRELOADED_STATE__.settings.env.PUBLIC_API]"}),
    ]

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response):
        for location in response.json()["items"]:
            self.pre_process_data(location)

            if location.get("status") != "Active":
                continue
            item = DictParser.parse(location)
            item["ref"] = location["retailerStoreId"]
            item["name"] = item["name"].strip()
            item["city"] = item["city"].strip()
            item["street_address"] = clean_address(
                [location.get("addressLine1"), location.get("addressLine2"), location.get("addressLine3")]
            )
            item["state"] = location.get("countyProvinceState")
            if location.get("openingHours"):
                item["opening_hours"] = OpeningHours()
                item["opening_hours"].add_ranges_from_string(location["openingHours"])
            yield from self.post_process_item(item, response, location) or []

    def pre_process_data(self, location, **kwargs):
        """Override with any pre-processing on the item."""

    def post_process_item(self, item: Feature, response: Response, location: dict) -> Iterable[Feature]:
        """Override with any post-processing on the item."""
        yield item
