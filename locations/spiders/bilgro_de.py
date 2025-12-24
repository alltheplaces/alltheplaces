from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.hours import DAYS_DE
from locations.items import Feature
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class BilgroDESpider(WPStoreLocatorSpider):
    name = "bilgro_de"
    item_attributes = {"brand_wikidata": "Q108029888", "brand": "bilgro"}
    allowed_domains = [
        "www.bilgro.de",
    ]
    days = DAYS_DE

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        apply_category(Categories.SHOP_BEVERAGES, item)
        yield item
