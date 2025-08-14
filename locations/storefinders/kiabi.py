from typing import Iterable

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.woosmap import WoosmapSpider


class KiabiSpider(WoosmapSpider):
    item_attributes = {"brand": "Kiabi", "brand_wikidata": "Q3196299"}

    def parse_item(self, item: Feature, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        item["name"] = "Kiabi"
        item["website"] = f'{self.origin}{item["website"]}'
        apply_category(Categories.SHOP_CLOTHES, item)
        yield item
