from typing import Iterable

from locations.categories import Categories
from locations.items import Feature
from locations.storefinders.sylinder import SylinderSpider


class MixNOSpider(SylinderSpider):
    name = "mix_no"
    item_attributes = {"brand": "Mix", "brand_wikidata": "Q56404240", "extras": Categories.SHOP_KIOSK.value}
    app_keys = ["1410"]
    warn_if_no_base_url = False

    def parse_item(self, item: Feature, location: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("MIX ")
        item["name"] = "MIX"
        yield item
