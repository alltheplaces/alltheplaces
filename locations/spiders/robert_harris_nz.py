from typing import Iterable

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.storemapper import StoremapperSpider


class RobertHarrisNZSpider(StoremapperSpider):
    name = "robert_harris_nz"
    item_attributes = {
        "brand_wikidata": "Q121652432",
        "brand": "Robert Harris",
    }
    company_id = "34028-1yjnEntNxRT3bUcl"

    def parse_item(self, item: Feature, location: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        apply_category(Categories.CAFE, item)
        yield item
