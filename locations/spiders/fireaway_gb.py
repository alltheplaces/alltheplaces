from typing import Iterable

from scrapy.http import Response

from locations.items import Feature
from locations.storefinders.agile_store_locator import AgileStoreLocatorSpider


class FireawayGBSpider(AgileStoreLocatorSpider):
    name = "fireaway_gb"
    allowed_domains = ["fireaway.co.uk"]
    item_attributes = {"brand_wikidata": "Q110484131"}

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("Fireaway ")
        item["website"] = None
        yield item
