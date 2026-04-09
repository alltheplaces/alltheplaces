from typing import Any, AsyncIterator, Iterable

from scrapy import Spider
from scrapy.http import JsonRequest, TextResponse

from locations.dict_parser import DictParser
from locations.items import Feature


class CanlySpider(Spider):
    """
    Can-ly (カンリー) is a software-as-a-service store locator API with an official
    website of https://jp.can-ly.com/

    To use this spider, supply a `brand_key` for a brand or operator's store
    locator which is hosted by Can-ly. Brand keys are numerical.
    """

    dataset_attributes: dict = {"source": "api", "api": "can-ly.com"}
    brand_key: str

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(url=f"https://g9ey9rioe.api.hp.can-ly.com/v2/companies/{self.brand_key}/shops/search")

    def parse(self, response: TextResponse, **kwargs: Any) -> Iterable[Feature]:
        for feature in response.json()["shops"]:
            self.pre_process_data(feature)

            item = DictParser.parse(feature)
            item["addr_full"] = feature.get("address")
            item["ref"] = feature.get("storeCode")

            yield from self.post_process_item(item, response, feature) or []

    def pre_process_data(self, feature: dict):
        """Override with any pre-processing on the item."""

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        """Override with any post-processing on the item."""
        yield item
