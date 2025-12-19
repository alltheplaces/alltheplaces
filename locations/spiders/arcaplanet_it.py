from typing import Any

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.yext import YextSpider


class ArcaplanetITSpider(YextSpider):
    name = "arcaplanet_it"
    item_attributes = {"brand": "Arcaplanet", "brand_wikidata": "Q105530937"}
    api_key = "e0faf99fdcbc6c43da0eaf74c90c23d1"
    api_version = "20220511"

    def parse_item(self, item: Feature, location: dict, **kwargs: Any) -> Any:
        apply_category(Categories.SHOP_PET, item)
        yield item
