from typing import Iterable

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.storemapper import StoremapperSpider


class BedsRUSAUSpider(StoremapperSpider):
    name = "beds_r_us_au"
    item_attributes = {"brand": "Beds R Us", "brand_wikidata": "Q126179491"}
    company_id = "27289-rJ0a0kvXQGRyNCLs"

    def parse_item(self, item: Feature, location: dict) -> Iterable[Feature]:
        apply_category(Categories.SHOP_BED, item)
        yield item
