from typing import Iterable

from chompjs import parse_js_object
from scrapy.http import JsonRequest, Request, Response

from locations.automatic_spider_generator import AutomaticSpiderGenerator, DetectionRequestRule
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import clean_address


class AmaiPromapSpider(JSONBlobSpider, AutomaticSpiderGenerator):
    """
    Marketing info here https://amai.com/apps/promap-store-locator/

    Indicator:
    Request to https://amaicdn.com/storelocator-prod/wtb/*.js

    To use this spider, simply specify a store page URL with `start_urls`; or directly point to the `js_urls`.
    """

    js_urls = []
    detection_rules = [
        DetectionRequestRule(url=r"^(?P<js_urls__list>https?:\/\/amaicdn\.com\/storelocator-prod\/wtb\/.*)")
    ]

    def start_requests(self):
        # Configured with storefinder pages, extract links
        if len(self.js_urls) == 0:
            for url in self.start_urls:
                yield Request(url=url, callback=self.detect_js)

        for url in self.js_urls:
            yield JsonRequest(url=url, callback=self.parse)

    def detect_js(self, response: Response):
        urls = parse_js_object(
            response.xpath('.//script[contains(text(), "var urls =")]/text()').get().split("var urls =")[1]
        )
        js_url = [u for u in urls if "amaicdn.com/storelocator-prod/wtb/" in u]  # should be only one
        for url in js_url:
            yield JsonRequest(url=url, callback=self.parse)

    def extract_json(self, response: Response):
        chunks = response.text.split("SCASLWtb=")
        return parse_js_object(chunks[1])["locations"]

    def parse_feature_array(self, response: Response, feature_array: list) -> Iterable[Feature]:
        for feature in feature_array:
            self.pre_process_data(feature)
            item = DictParser.parse(feature)

            if hours_raw := feature.get("operating_hours"):
                item["opening_hours"] = OpeningHours()
                hours_dict = parse_js_object(hours_raw)
                for day_key, day_value in hours_dict.items():
                    for time in day_value["slot"]:
                        item["opening_hours"].add_range(day_value["name"], time["from"], time["to"])

            elif schedule := feature.get("schedule"):
                item["opening_hours"] = OpeningHours()
                for day in schedule.split("\n"):
                    item["opening_hours"].add_ranges_from_string(day)

            item["image"] = feature.get("store_image")
            item.pop("addr_full")
            item["street_address"] = clean_address([feature.get("address"), feature.get("address2")])
            yield from self.post_process_item(item, response, feature) or []
