from typing import Iterable

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.storepoint import StorepointSpider


class DavidsTeaCASpider(StorepointSpider):
    name = "davids_tea_ca"
    item_attributes = {"brand": "DavidsTea", "brand_wikidata": "Q3019129"}
    key = "169e0f2540d9e8"

    def parse_item(self, item: Feature, location: dict, **kwargs) -> Iterable[Feature]:
        item["ref"] = str(location["id"])
        item["branch"] = item.pop("name").removeprefix("DAVIDsTEA ")
        apply_category(Categories.SHOP_TEA, item)
        yield item
