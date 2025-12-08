from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_EN
from locations.items import Feature
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class AdriaticFurnitureAUSpider(WPStoreLocatorSpider):
    name = "adriatic_furniture_au"
    item_attributes = {"brand": "Adriatic Furniture", "brand_wikidata": "Q117856796"}
    allowed_domains = ["www.adriatic.com.au"]
    days = DAYS_EN

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        apply_category(Categories.SHOP_FURNITURE, item)
        yield item
