import re
from typing import Iterable

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.storerocket import StoreRocketSpider


class ChaiiwalaAECAGBSpider(StoreRocketSpider):
    name = "chaiiwala_ae_ca_gb"
    item_attributes = {"brand": "Chaiiwala", "brand_wikidata": "Q124478909"}
    storerocket_id = "dQ8daoEpr1"
    iseadgg_countries_list = ["AE", "CA", "GB"]
    search_radius = 1000

    def parse_item(self, item: Feature, location: dict) -> Iterable[Feature]:
        item["branch"] = re.sub(r"^chaiiwala®?\s*(of London\s*-\s*)?", "", item.pop("name"), flags=re.IGNORECASE)
        apply_category(Categories.CAFE, item)
        yield item
