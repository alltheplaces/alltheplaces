from typing import Iterable

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.storepoint import StorepointSpider


class HotterGBSpider(StorepointSpider):
    name = "hotter_gb"
    item_attributes = {"brand": "Hotter", "brand_wikidata": "Q91919346"}
    key = "16ada08f360ff1"

    def parse_item(self, item: Feature, location: dict, **kwargs) -> Iterable[Feature]:
        location_type = location.get("tags") or ""
        if location_type.lower() == "stockist":
            return
        item["branch"] = item.pop("name", None)
        apply_category(Categories.SHOP_SHOES, item)
        yield item
