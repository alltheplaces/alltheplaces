from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.spiders.pizza_hut_gb import PizzaHutGBSpider


class PizzaHutFRSpider(PizzaHutGBSpider):
    name = "pizza_hut_fr"
    item_attributes = {"brand": "Pizza Hut", "brand_wikidata": "Q191615"}
    start_urls = ["https://api.pizzahut.io/v1/huts/?sector=fr-1"]

    def post_process_item(self, item: Feature, response: Response, location: dict, **kwargs) -> Iterable[Feature]:
        if location["type"] == "restaurant":
            apply_category(Categories.RESTAURANT, item)
        elif location["type"] == "delivery":
            apply_category(Categories.FAST_FOOD, item)
        yield item
