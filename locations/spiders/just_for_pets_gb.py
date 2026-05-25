from typing import Iterable

from locations.categories import Categories
from locations.items import Feature
from locations.storefinders.storemapper import StoremapperSpider


class JustForPetsGBSpider(StoremapperSpider):
    name = "just_for_pets_gb"
    item_attributes = {"brand": "Just For Pets", "name": "Just For Pets", "extras": Categories.SHOP_PET.value}
    company_id = "10020"

    def parse_item(self, item: Feature, location: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        yield item
