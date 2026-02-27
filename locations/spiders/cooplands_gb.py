from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.hours import DAYS_EN
from locations.items import Feature
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class CooplandsGBSpider(WPStoreLocatorSpider):
    name = "cooplands_gb"
    item_attributes = {"brand": "Cooplands", "brand_wikidata": "Q5167971"}
    allowed_domains = ["cooplands-bakery.co.uk"]
    iseadgg_countries_list = ["GB"]
    search_radius = 24
    max_results = 50
    days = DAYS_EN

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        apply_category(Categories.SHOP_BAKERY, item)
        yield item
