from typing import Iterable

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.sylinder import SylinderSpider


class SnarkjopNOSpider(SylinderSpider):
    name = "snarkjop_no"
    item_attributes = {"name": "Snarkjøp", "brand": "Snarkjøp"}
    app_keys = ["4150"]
    warn_if_no_base_url = False

    def parse_item(self, item: Feature, location: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("Snarkjøp ").removesuffix(" DV")
        apply_category(Categories.SHOP_CONVENIENCE, item)
        yield item
