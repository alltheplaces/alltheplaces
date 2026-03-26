from typing import Iterable

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.storepoint import StorepointSpider


class TousLesJoursSpider(StorepointSpider):
    name = "tous_les_jours"
    item_attributes = {"brand": "Tous les Jours", "brand_wikidata": "Q3535609"}
    key = "1644aa2ac5115c"

    def parse_item(self, item: Feature, location: dict, **kwargs) -> Iterable[Feature]:
        if "[COMING SOON]" in item["name"]:
            return
        item["branch"] = item.pop("name")
        item["website"] = None
        apply_category(Categories.SHOP_BAKERY, item)
        yield item
