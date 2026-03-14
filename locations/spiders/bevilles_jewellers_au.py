from typing import Iterable

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.storemapper import StoremapperSpider


class BevillesJewellersAUSpider(StoremapperSpider):
    name = "bevilles_jewellers_au"
    item_attributes = {
        "brand": "Bevilles Jewellers",
        "brand_wikidata": "Q117837188",
    }
    company_id = "6228"

    def parse_item(self, item: Feature, location: dict) -> Iterable[Feature]:
        item["name"] = item["name"].replace(" | ", " ")
        item["branch"] = item["name"].replace("Bevilles Jewellers ", "")
        apply_category(Categories.SHOP_JEWELRY, item)
        yield item
