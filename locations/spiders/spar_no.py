from typing import Iterable

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.spiders.spar_aspiag import SPAR_SHARED_ATTRIBUTES
from locations.storefinders.sylinder import SylinderSpider


class SparNOSpider(SylinderSpider):
    name = "spar_no"
    item_attributes = SPAR_SHARED_ATTRIBUTES
    app_keys = ["1210"]
    base_url = "https://spar.no/finn-butikk/"

    def parse_item(self, item: Feature, location: dict) -> Iterable[Feature]:
        raw_name = item.pop("name")
        if raw_name.startswith("EUROSPAR "):
            item["name"] = "Eurospar"
            item["branch"] = raw_name.removeprefix("EUROSPAR ")
        else:
            item["name"] = "Spar"
            item["branch"] = raw_name.removeprefix("SPAR ")
        apply_category(Categories.SHOP_SUPERMARKET, item)
        yield item
