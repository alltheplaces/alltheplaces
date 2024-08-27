from typing import Iterable

from scrapy.http import Response

from locations.items import Feature
from locations.storefinders.storefrontgateway import StorefrontgatewaySpider


class FreshThymeUSSpider(StorefrontgatewaySpider):
    name = "fresh_thyme_us"
    item_attributes = {"brand": "Fresh Thyme", "brand_wikidata": "Q64132791"}
    start_urls = ["https://storefrontgateway.freshthyme.com/api/stores"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item.pop("name", None)
        yield item
