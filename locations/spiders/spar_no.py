from typing import Iterable

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.spiders.spar_aspiag import SPAR_SHARED_ATTRIBUTES
from locations.storefinders.sylinder import SylinderSpider


class SparNOSpider(SylinderSpider):
    name = "spar_no"
    item_attributes = SPAR_SHARED_ATTRIBUTES
    app_key = "1210"
    base_url = "https://spar.no/Finn-butikk/"

    def parse_item(self, item: Feature, location: dict) -> Iterable[Feature]:
        if item["name"].startswith("EUROSPAR "):
            item["branch"] = item.pop("name").removeprefix("EUROSPAR ")
            item["name"] = "Eurospar"
        elif item["name"].startswith("SPAR "):
            item["branch"] = item.pop("name").removeprefix("SPAR ")
            item["name"] = "Spar"
        apply_category(Categories.SHOP_SUPERMARKET, item)
        yield item
