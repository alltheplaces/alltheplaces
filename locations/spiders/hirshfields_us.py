from typing import Iterable

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.storepoint import StorepointSpider


class HirshfieldsUSSpider(StorepointSpider):
    name = "hirshfields_us"
    item_attributes = {"name": "Hirshfield's"}
    key = "15ccc5a657ee36"
    drop_attributes = {"twitter", "facebook"}

    def parse_item(self, item: Feature, location: dict, **kwargs) -> Iterable[Feature]:
        item["ref"] = str(location["id"])
        item["branch"] = " ".join(item.pop("name").removeprefix("Hirshfield's").split())
        apply_category(Categories.SHOP_PAINT, item)
        yield item
