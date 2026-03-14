from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.agile_store_locator import AgileStoreLocatorSpider


class ShopMetroPHSpider(AgileStoreLocatorSpider):
    name = "shop_metro_ph"
    allowed_domains = [
        "shopmetro.ph",
    ]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        description = feature.get("description", "")
        if "Super Metro" in item["name"]:
            item["brand"] = "Super Metro"
            item["brand_wikidata"] = "Q23808789"
            apply_category(Categories.SHOP_SUPERMARKET, item)
        elif "Department Store" in description:
            item["brand"] = "Metro Department Store"
            item["brand_wikidata"] = "Q23808789"
            apply_category(Categories.SHOP_DEPARTMENT_STORE, item)
        elif "Supermarket" in description:
            item["brand"] = "Metro Supermarket"
            item["brand_wikidata"] = "Q23808789"
            apply_category(Categories.SHOP_SUPERMARKET, item)
        yield item
