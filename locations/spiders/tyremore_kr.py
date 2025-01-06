from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.spiders.tyreplus_au import TyreplusAUSpider


class TyremoreKRSpider(TyreplusAUSpider):
    name = "tyremore_kr"
    item_attributes = {"brand": "Tyremore", "brand_wikidata": "Q131681197"}
    allowed_domains = ["www.tyremore.co.kr"]
    start_urls = ["https://www.tyremore.co.kr/ko/%EC%84%BC%ED%84%B0"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("타이어모어 ")
        apply_category(Categories.SHOP_TYRES, item)
        yield item
