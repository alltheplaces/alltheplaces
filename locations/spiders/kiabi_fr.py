from typing import Iterable
from urllib.parse import urljoin

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.woosmap import WoosmapSpider


class KiabiFRSpider(WoosmapSpider):
    name = "kiabi_fr"
    item_attributes = {"brand": "Kiabi", "brand_wikidata": "Q3196299"}

    key = "woos-3246a080-0b90-39a2-a673-5ae6b9acb1d9"
    origin = "https://www.kiabi.com"

    def parse_item(self, item: Feature, feature: dict) -> Iterable[Feature]:
        item["website"] = urljoin(self.origin, item["website"])
        item["branch"] = item.pop("name")
        apply_category(Categories.SHOP_CLOTHES, item)
        yield item
