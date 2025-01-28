from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.spiders.tyreplus_au import TyreplusAUSpider


class TyreplusTWSpider(TyreplusAUSpider):
    name = "tyreplus_tw"
    allowed_domains = ["tyreplus.com.tw"]
    start_urls = ["https://tyreplus.com.tw/dealers"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("米其林馳加汽車服務中心-")
        apply_category(Categories.SHOP_TYRES, item)
        yield item
