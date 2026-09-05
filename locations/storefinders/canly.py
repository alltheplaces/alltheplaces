import json
from typing import Any, AsyncIterator, Iterable

from scrapy import Spider
from scrapy.http import JsonRequest, Request, TextResponse

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature


class CanlySpider(Spider):
    """
    Can-ly (カンリー) is a software-as-a-service store locator API with an official
    website of https://jp.can-ly.com/

    To use this spider, supply a `brand_key` for a brand or operator's store
    locator which is hosted by Can-ly. Brand keys are numerical.
    """

    api_endpoint: str = ""
    dataset_attributes: dict = {"source": "api", "api": "can-ly.com"}
    brand_key: str = ""

    async def start(self) -> AsyncIterator[JsonRequest]:
        if self.api_endpoint == "" and self.brand_key != "":
            yield JsonRequest(url=f"https://g9ey9rioe.api.hp.can-ly.com/v2/companies/{self.brand_key}/shops/search")
        else:
            yield JsonRequest(url=self.api_endpoint)

    def parse(self, response: TextResponse, **kwargs: Any) -> Iterable[Feature]:
        for feature in response.json()["shops"]:
            self.pre_process_data(feature)

            item = DictParser.parse(feature)
            item["addr_full"] = feature.get("address")
            item["ref"] = feature.get("storeCode")

            oh = OpeningHours()
            if item_hours := feature.get("businessHours"):
                for day_hours in item_hours:
                    oh.add_range(day_hours["name"], day_hours["openTime"], day_hours["closeTime"], "%H:%M:%S")
            item["opening_hours"] = oh

            if self._fetches_detail_pages():
                for prepared in self.post_process_item(item, response, feature) or []:
                    if website := prepared.get("website"):
                        yield Request(
                            url=website, callback=self.parse_detail, meta={"item": prepared, "feature": feature}
                        )
                    else:
                        yield prepared
            else:
                yield from self.post_process_item(item, response, feature) or []

    def _fetches_detail_pages(self) -> bool:
        # Override `post_process_detail` in a subclass to opt in to fetching each
        # shop's detail page (the URL set as `item["website"]` in
        # `post_process_item`) and decorating the item from its `__NEXT_DATA__`.
        return type(self).post_process_detail is not CanlySpider.post_process_detail

    def parse_detail(self, response: TextResponse) -> Iterable[Feature]:
        item = response.meta["item"]
        feature = response.meta["feature"]
        data = json.loads(response.xpath('//script[@id="__NEXT_DATA__"]/text()').get())
        cms_item_values = data["props"]["pageProps"]["shop"]["cmsItemValues"]
        yield from self.post_process_detail(item, response, feature, cms_item_values) or []

    def pre_process_data(self, feature: dict):
        """Override with any pre-processing on the item."""

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        """Override with any post-processing on the item."""
        yield item

    def post_process_detail(
        self, item: Feature, response: TextResponse, feature: dict, cms_item_values: list
    ) -> Iterable[Feature]:
        """Override to decorate the item from a shop's detail page content.

        Receives the shop's `cmsItemValues` from the detail page `__NEXT_DATA__`;
        only data absent from the main API response. Overriding this method opts
        the spider in to fetching detail pages; it is called in addition to
        `post_process_item`.
        """
        yield item
