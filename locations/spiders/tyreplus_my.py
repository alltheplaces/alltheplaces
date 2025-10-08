from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.spiders.tyreplus_au import TyreplusAUSpider


class TyreplusMYSpider(TyreplusAUSpider):
    name = "tyreplus_my"
    allowed_domains = ["tyreplus.com.my"]
    start_urls = ["https://tyreplus.com.my/dealers"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("Tyreplus - ").removeprefix("TYREPLUS - ")
        apply_category(Categories.SHOP_TYRES, item)
        yield item
