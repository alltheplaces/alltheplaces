from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.spiders.tyreplus_au import TyreplusAUSpider


class TyreplusTHSpider(TyreplusAUSpider):
    name = "tyreplus_th"
    allowed_domains = ["www.tyreplus.co.th"]
    start_urls = ["https://www.tyreplus.co.th/dealers"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("ไทร์พลัส ")
        apply_category(Categories.SHOP_TYRES, item)
        yield item
