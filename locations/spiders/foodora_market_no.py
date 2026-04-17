from typing import Iterable

from locations.categories import Categories
from locations.items import Feature
from locations.storefinders.sylinder import SylinderSpider


class FoodoraMarketNOSpider(SylinderSpider):
    name = "foodora_market_no"
    item_attributes = {
        "brand": "Foodora Market",
        "brand_wikidata": "Q24068412",
        "extras": Categories.DARK_STORE_GROCERY.value,
    }
    app_keys = ["4140"]
    warn_if_no_base_url = False

    def parse_item(self, item: Feature, location: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("Foodora Market ").removesuffix(" DV")
        item["name"] = "Foodora Market"
        yield item
