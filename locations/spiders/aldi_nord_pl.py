from typing import Iterable

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.uberall import UberallSpider


class AldiNordPLSpider(UberallSpider):
    name = "aldi_nord_pl"
    item_attributes = {"brand_wikidata": "Q41171373"}
    key = "ALDINORDPL_3Lul0K0H0Vy47Jz0wGZlN30mchboaO"

    def post_process_item(self, item: Feature, response, feature: dict) -> Iterable[Feature]:
        if item["name"] == "ALDI [W budowie]":
            return  # Construction

        item["name"] = None  # Take casing from NSI

        apply_category(Categories.SHOP_SUPERMARKET, item)

        yield item
