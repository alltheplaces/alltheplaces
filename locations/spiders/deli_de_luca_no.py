from typing import Iterable

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.sylinder import SylinderSpider


class DeliDeLucaNOSpider(SylinderSpider):
    name = "deli_de_luca_no"
    item_attributes = {"name": "Deli de Luca", "brand": "Deli de Luca", "brand_wikidata": "Q11965047"}
    app_keys = ["1800"]
    warn_if_no_base_url = False

    def parse_item(self, item: Feature, location: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("Deli de Luca ")

        apply_category(Categories.SHOP_CONVENIENCE, item)

        yield item
