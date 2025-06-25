from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.agile_store_locator import AgileStoreLocatorSpider


class ShahsHalalFoodUSSpider(AgileStoreLocatorSpider):
    name = "shahs_halal_food_us"
    item_attributes = {"brand": "Shah's Halal Food", "brand_wikidata": "Q135009954"}
    allowed_domains = ["www.shahshalalfood.com"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name", None)
        apply_category(Categories.FAST_FOOD, item)
        yield item
