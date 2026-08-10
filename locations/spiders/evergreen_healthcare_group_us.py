from typing import Iterable

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.storepoint import StorepointSpider


class EvergreenHealthcareGroupUSSpider(StorepointSpider):
    name = "evergreen_healthcare_group_us"
    item_attributes = {"operator": "Evergreen Healthcare Group"}
    key = "1679a3dab2f71f"

    def parse_item(self, item: Feature, location: dict, **kwargs) -> Iterable[Feature]:
        apply_category(Categories.CLINIC, item)
        yield item
