from typing import Iterable

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.storemapper import StoremapperSpider


class JustForPetsGBSpider(StoremapperSpider):
    name = "just_for_pets_gb"
    item_attributes = {"name": "Just For Pets", "brand": "Just For Pets"}
    company_id = "10020"

    def parse_item(self, item: Feature, location: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name")

        apply_category(Categories.SHOP_PET, item)

        yield item
