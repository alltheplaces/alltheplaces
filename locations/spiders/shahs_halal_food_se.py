from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.spiders.shahs_halal_food_us import ShahsHalalFoodUSSpider


class ShahsHalalFoodSESpider(ShahsHalalFoodUSSpider):
    name = "shahs_halal_food_se"
    allowed_domains = ["www.shahshalalfood.se"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name", None)
        apply_category(Categories.FAST_FOOD, item)
        yield item
