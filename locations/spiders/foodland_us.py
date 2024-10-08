from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories
from locations.items import Feature
from locations.storefinders.agile_store_locator import AgileStoreLocatorSpider


class FoodlandUSSpider(AgileStoreLocatorSpider):
    name = "foodland_us"
    item_attributes = {"extras": Categories.SHOP_SUPERMARKET.value}
    allowed_domains = ["foodland.com"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if feature["title"].startswith("Foodland Farms "):
            item["brand"] = "Foodland Farms"
            item["brand_wikidata"] = "Q124987342"
        elif feature["title"].startswith("Foodland "):
            item["brand"] = "Foodland"
            item["brand_wikidata"] = "Q5465560"
        elif feature["title"].startswith("Sack N Save "):
            item["brand"] = "Sack 'N Save"
            item["brand_wikidata"] = "Q124987338"
        yield item
