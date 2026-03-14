from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.hours import DAYS_EN
from locations.items import Feature
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class BrewingzUSSpider(WPStoreLocatorSpider):
    name = "brewingz_us"
    item_attributes = {"brand": "BreWingZ", "brand_wikidata": "Q123022531"}
    allowed_domains = ["www.brewingz.com"]
    days = DAYS_EN

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        apply_category(Categories.RESTAURANT, item)
        yield item
