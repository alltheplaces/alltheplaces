from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.agile_store_locator import AgileStoreLocatorSpider


class TomMarketHUSpider(AgileStoreLocatorSpider):
    name = "tom_market_hu"
    item_attributes = {"brand": "Tom Market", "name": "Tom Market"}
    allowed_domains = ["tommarket.hu"]

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("Tom Market").strip()
        apply_category(Categories.SHOP_CONVENIENCE, item)
        yield item
