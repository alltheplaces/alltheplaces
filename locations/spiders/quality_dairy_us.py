from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.agile_store_locator import AgileStoreLocatorSpider


class QualityDairyUSSpider(AgileStoreLocatorSpider):
    name = "quality_dairy_us"
    item_attributes = {"brand": "Quality Dairy", "brand_wikidata": "Q23461886"}
    allowed_domains = ["qualitydairy.com"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.get("name", "").removeprefix("Quality Dairy Store - ")
        apply_category(Categories.SHOP_CONVENIENCE, item)
        yield item
