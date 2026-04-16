from typing import Iterable

from locations.categories import Categories
from locations.items import Feature
from locations.storefinders.sylinder import SylinderSpider


class SnarkjopNOSpider(SylinderSpider):
    name = "snarkjop_no"
    item_attributes = {"brand": "Snarkjøp", "extras": Categories.SHOP_CONVENIENCE.value}
    app_keys = ["4150"]
    base_url = (
        "https://www.snarkjop.no/butikkene/#"  # Kind of a hack. The website doesn't have the storefinder in place.
    )

    def parse_item(self, item: Feature, location: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("Snarkjøp ").removesuffix(" DV")
        item["name"] = "Snarkjøp"
        yield item
