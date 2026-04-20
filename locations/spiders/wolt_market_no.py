from typing import Iterable

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.sylinder import SylinderSpider


class WoltMarketNOSpider(SylinderSpider):
    name = "wolt_market_no"
    item_attributes = {"name": "Wolt Market", "brand": "Wolt Market", "brand_wikidata": "Q30024526"}
    app_keys = ["4220"]
    warn_if_no_base_url = False

    def parse_item(self, item: Feature, location: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("Wolt Market ").removesuffix(" DV")
        apply_category(Categories.DARK_STORE_GROCERY.value, item)
        yield item
