from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.spiders.tyreplus_au import TyreplusAUSpider


class TyreplusOMSpider(TyreplusAUSpider):
    name = "tyreplus_om"
    allowed_domains = ["www.tyreplus-me.com"]
    start_urls = ["https://www.tyreplus-me.com/en/oman/dealers"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("TYREPLUS - ").removeprefix("TYREPLUS ")
        apply_category(Categories.SHOP_TYRES, item)
        yield item
