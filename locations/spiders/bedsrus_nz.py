from typing import Iterable

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.storemapper import StoremapperSpider


class BedsrusNZSpider(StoremapperSpider):
    name = "bedsrus_nz"
    item_attributes = {"brand": "BedsRus", "brand_wikidata": "Q111018938"}
    company_id = "16389"

    def parse_item(self, item: Feature, location: dict) -> Iterable[Feature]:
        item["branch"] = item["name"].replace("BedsRus ", "")
        apply_category(Categories.SHOP_BED, item)
        yield item
