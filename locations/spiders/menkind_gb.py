from typing import Iterable

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.storerocket import StoreRocketSpider


class MenkindGBSpider(StoreRocketSpider):
    name = "menkind_gb"
    item_attributes = {"brand": "Menkind", "brand_wikidata": "Q66725844"}
    storerocket_id = "VyJzzwEJ6M"

    def parse_item(self, item: Feature, location: dict, **kwargs) -> Iterable[Feature]:
        item["branch"] = item.pop("name").replace("MENKIND", "").strip()
        apply_category(Categories.SHOP_GIFT, item)
        yield item
