from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.spiders.tyreplus_au import TyreplusAUSpider


class TyreplusKWSpider(TyreplusAUSpider):
    name = "tyreplus_kw"
    allowed_domains = ["www.tyreplus-me.com"]
    start_urls = ["https://www.tyreplus-me.com/en/kuwait/dealers"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("TYREPLUS ").removeprefix("Tyreplus ")
        apply_category(Categories.SHOP_TYRES, item)
        yield item
