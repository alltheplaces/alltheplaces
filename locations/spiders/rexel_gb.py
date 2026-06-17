from typing import Iterable

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.rexel import RexelSpider

REXEL = {"brand": "Rexel", "brand_wikidata": "Q962489"}
DENMANS = {"brand": "Denmans", "brand_wikidata": "Q116508855"}


class RexelGBSpider(RexelSpider):
    name = "rexel_gb"
    base_url = "www.rexel.co.uk/uki"
    search_lat = 51
    search_lon = -0
    drop_attributes = {"image"}

    def parse_item(self, item: Feature, feature: dict, **kwargs) -> Iterable[Feature]:
        if item["name"].startswith("Rexel "):
            item["branch"] = item.pop("name").replace("Rexel ", "")
            item.update(REXEL)
        elif item["name"].startswith("Denmans "):
            item["branch"] = item.pop("name").replace("Denmans ", "")
            item.update(DENMANS)

        apply_category(Categories.SHOP_ELECTRICAL, item)

        yield item
