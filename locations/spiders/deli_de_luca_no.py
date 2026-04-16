from typing import Iterable

from locations.categories import Categories
from locations.items import Feature
from locations.storefinders.sylinder import SylinderSpider


class DeliDeLucaNOSpider(SylinderSpider):
    name = "deli_de_luca_no"
    item_attributes = {
        "brand": "Deli de Luca",
        "brand_wikidata": "Q11965047",
        "extras": Categories.SHOP_CONVENIENCE.value,
    }
    app_keys = ["1800"]
    base_url = "https://delideluca.no/finn-oss/#"  # Kind of a hack. The website doesn't have the storefinder in place.

    def parse_item(self, item: Feature, location: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("Deli de Luca ")
        item["name"] = "Deli de Luca"
        yield item
