from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.hours import DAYS_DE
from locations.items import Feature
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class BarbarossaBaeckereiDESpider(WPStoreLocatorSpider):
    name = "barbarossa_baeckerei_de"
    item_attributes = {
        "brand_wikidata": "Q807766",
        "brand": "Barbarossa Bäckerei",
    }
    allowed_domains = [
        "www.barbarossa-baeckerei.de",
    ]
    days = DAYS_DE

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        apply_category(Categories.SHOP_BAKERY, item)
        yield item
