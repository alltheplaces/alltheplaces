from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.agile_store_locator import AgileStoreLocatorSpider


class HipermaxiBOSpider(AgileStoreLocatorSpider):
    name = "hipermaxi_bo"
    item_attributes = {
        "brand_wikidata": "Q81968262",
        "brand": "Hipermaxi",
    }
    allowed_domains = [
        "hipermaxi.com",
    ]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if feature["slug"].startswith("farmacia-"):
            apply_category(Categories.PHARMACY, item)
        if feature["slug"].startswith("drugstore-"):
            apply_category(Categories.SHOP_CHEMIST, item)
        if feature["slug"].startswith("hipermaxi-"):
            apply_category(Categories.SHOP_SUPERMARKET, item)
        yield item
