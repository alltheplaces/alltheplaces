from typing import AsyncIterator, Iterable

from chompjs import parse_js_object
from scrapy.http import JsonRequest, Request, TextResponse

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines


class AmaiPromapSpider(JSONBlobSpider):
    """
    Amai ProMap or Rose Perl (RP) ProMap are self-hosted Shopify plugin
    storefinders, with an official website of:
    https://apps.shopify.com/store-locator-4

    To use this spider, simply specify a store page URL as a single item
    within the `start_urls` list attribute.
    """

    start_urls: list[str] = []
    _locators: list[str] = ["amaicdn", "roseperl"]  # Amai ProMap is same as Rose Perl ProMap

    async def start(self) -> AsyncIterator[Request]:
        if len(self.start_urls) != 1:
            raise ValueError("Specify one URL in the start_urls list attribute.")
            return
        yield Request(url=self.start_urls[0], callback=self.fetch_js)

    def fetch_js(self, response: TextResponse) -> Iterable[JsonRequest]:
        urls = parse_js_object(
            response.xpath('.//script[contains(text(), "var urls =")]/text()').get().split("var urls =")[1]
        )
        js_url = [
            u for u in urls if any(f"{locator}.com/storelocator-prod/wtb/" in u for locator in self._locators)
        ]  # should be only one
        for url in js_url:
            yield JsonRequest(url=url, callback=self.parse)

    def extract_json(self, response: TextResponse) -> dict:
        chunks = response.text.split("SCASLWtb=")
        return parse_js_object(chunks[1])["locations"]

    def parse_feature_array(self, response: TextResponse, feature_array: list) -> Iterable[Feature]:
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
            item["street_address"] = merge_address_lines([feature.get("address"), feature.get("address2")])
            yield from self.post_process_item(item, response, feature) or []
