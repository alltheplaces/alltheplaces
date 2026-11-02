from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.agile_store_locator import AgileStoreLocatorSpider


class ChiefMarketsUSSpider(AgileStoreLocatorSpider):
    name = "chief_markets_us"
    item_attributes = {"brand": "Chief Markets"}
    allowed_domains = ["chiefmarkets.com"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["id"]
        item["branch"] = item.pop("name", None)
        item["website"] = None
        item["extras"].pop("description", None)

        apply_category(Categories.SHOP_SUPERMARKET, item)

        yield item
