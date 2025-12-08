from typing import Any

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.yext import YextSpider

BRANDS = {
    "https://www.bravosupermarkets.com": {"brand": "Bravo", "brand_wikidata": "Q16985159"},
    "https://www.ctownsupermarkets.com": {"brand": "C-Town Supermarkets", "brand_wikidata": "Q5005929"},
}


class BravoUSSpider(YextSpider):
    name = "bravo_us"
    api_key = "62850d78675a712e91b03d1d5868d470"

    def parse_item(self, item: Feature, location: dict, **kwargs: Any) -> Any:
        if brand := BRANDS.get(location.get("c_brandURL")):
            item["name"] = None
            item.update(brand)

        apply_category(Categories.SHOP_SUPERMARKET, item)

        yield item
