from typing import Iterable

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.dict_parser import DictParser
from locations.items import Feature


class ClosebySpider(Spider):
    """
    Closeby is a software-as-a-service store locator API with an official
    website of https://www.closeby.co/

    To use this spider, supply a `api_key` for a brand or operator's store
    locator which is hosted by Closeby. API keys are a 32 character long
    hexademical value (regex: [\da-f]{32}).
    """

    dataset_attributes = {"source": "api", "api": "closeby.co"}
    api_key: str = ""

    def start_requests(self) -> Iterable[JsonRequest]:
        yield JsonRequest(url=f"https://www.closeby.co/embed/{self.api_key}/locations")

    def parse(self, response: Response) -> Iterable[Feature]:
        for feature in response.json()["locations"]:
            self.pre_process_data(feature)

            item = DictParser.parse(feature)
            item["addr_full"] = feature.get("address_full")

            yield from self.post_process_item(item, response, feature) or []

    def pre_process_data(self, feature: dict) -> dict:
        """Override with any pre-processing on the item."""

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        """Override with any post-processing on the item."""
        yield item
