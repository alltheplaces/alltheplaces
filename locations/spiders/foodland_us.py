from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.agile_store_locator import AgileStoreLocatorSpider


class FoodlandUSSpider(AgileStoreLocatorSpider):
    name = "foodland_us"
    item_attributes = {"brand": "Foodland", "brand_wikidata": "Q5465560"}
    allowed_domains = ["foodland.com"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if item["name"].startswith("Foodland Gas Station "):
            item["branch"] = item.pop("name").removeprefix("Foodland Gas Station ")
            item["nsi_id"] = "N/A"
            item["name"] = "Foodland"
            apply_category(Categories.FUEL_STATION, item)
        elif item["name"].startswith("Foodland Farms "):
            item["branch"] = item.pop("name").removeprefix("Foodland Farms ")
            item["name"] = "Foodland Farms"
            apply_category(Categories.SHOP_SUPERMARKET, item)
        elif item["name"].startswith("Foodland "):
            item["branch"] = item.pop("name").removeprefix("Foodland ")
            apply_category(Categories.SHOP_SUPERMARKET, item)
        elif item["name"].startswith("Sack N Save Gas n Go "):
            item["branch"] = item.pop("name").removeprefix("Sack N Save Gas n Go ")
            item["brand"] = "Sack 'N Save"
            item["name"] = "Sack 'N Save Gas n Go"
            item["brand_wikidata"] = "Q124987338"
            apply_category(Categories.FUEL_STATION, item)
        elif item["name"].startswith("Sack N Save "):
            item["branch"] = item.pop("name").removeprefix("Sack N Save ")
            item["name"] = item["brand"] = "Sack 'N Save"
            item["brand_wikidata"] = "Q124987338"
            apply_category(Categories.SHOP_SUPERMARKET, item)

        item["website"] = "https://foodland.com/stores/{}/".format(feature["slug"])

        yield item
