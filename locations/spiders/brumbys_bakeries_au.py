from typing import Iterable

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.storepoint import StorepointSpider


class BrumbysBakeriesAUSpider(StorepointSpider):
    name = "brumbys_bakeries_au"
    item_attributes = {
        "brand": "Brumby's Bakeries",
        "brand_wikidata": "Q4978794",
    }
    key = "167231a6e2f944"

    def parse_item(self, item: Feature, location: dict, **kwargs) -> Iterable[Feature]:
        apply_category(Categories.SHOP_BAKERY, item)
        yield item
