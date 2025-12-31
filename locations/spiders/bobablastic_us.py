from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.hours import DAYS_EN
from locations.items import Feature
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class BobablasticUSSpider(WPStoreLocatorSpider):
    name = "bobablastic_us"
    item_attributes = {"brand_wikidata": "Q108499280", "brand": "Bobablastic"}
    allowed_domains = [
        "bobablastic.com",
    ]
    iseadgg_countries_list = ["US"]
    search_radius = 100
    max_results = 50
    days = DAYS_EN

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        apply_category(Categories.FAST_FOOD, item)
        yield item
