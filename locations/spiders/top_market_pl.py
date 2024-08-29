from typing import Iterable

from scrapy.http import Response

from locations.items import Feature
from locations.storefinders.agile_store_locator import AgileStoreLocatorSpider


class TopMarketPLSpider(AgileStoreLocatorSpider):
    name = "top_market_pl"
    item_attributes = {"brand": "Top Market", "brand_wikidata": "Q9360044"}
    allowed_domains = ["www.topmarkety.pl"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        del item["website"]
        yield item
