from typing import Iterable

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.woosmap import WoosmapSpider


class MaisonsDuMondeSpider(WoosmapSpider):
    name = "maisons_du_monde"
    item_attributes = {"brand": "Maisons du Monde", "brand_wikidata": "Q3280364"}
    key = "woos-a4fa4367-383c-31c0-9d45-405ddae5a6da"
    origin = "https://www.maisonsdumonde.com"

    def parse_item(self, item: Feature, feature: dict) -> Iterable[Feature]:
        item.pop("name")
        apply_category(Categories.SHOP_FURNITURE, item)
        yield item
