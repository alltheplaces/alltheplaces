import re
from typing import Iterable

from scrapy.http import Response

from locations.items import Feature
from locations.storefinders.agile_store_locator import AgileStoreLocatorSpider


class FoodlandGroceryUSSpider(AgileStoreLocatorSpider):
    name = "foodland_grocery_us"
    item_attributes = {"brand": "FoodLand", "brand_wikidata": "Q5465271"}
    allowed_domains = ["www.foodlandgrocery.com"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if item["name"].endswith(" Foodland Plus"):
            item["branch"] = item.pop("name").removesuffix(" Foodland Plus")
            item["name"] = "FoodLand Plus"
        else:
            item["branch"] = item.pop("name").removesuffix(" Foodland")

        if m := re.search(r"store-locations/([^/]+)/$", item.pop("website")):
            item["website"] = "https://www.foodlandgrocery.com/store-locations/{}/".format(m.group(1))

        yield item
