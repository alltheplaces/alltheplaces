from typing import Iterable

from chompjs import parse_js_object
from scrapy.http import JsonRequest, Request, Response

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import clean_address


class AmaiPromapSpider(JSONBlobSpider):
    """
    To use this spider, simply specify a store page URL with `start_urls`.
    """

    def start_requests(self):
        for url in self.start_urls:
            yield Request(url=url, callback=self.fetch_js)

    def fetch_js(self, response: Response):
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
