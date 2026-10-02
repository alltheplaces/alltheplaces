from typing import Iterable

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.storerocket import StoreRocketSpider


class JetGBSpider(StoreRocketSpider):
    name = "jet_gb"
    item_attributes = {"brand": "JET", "brand_wikidata": "Q568940"}
    storerocket_id = "2BkJ1wEpqR"
    base_url = "https://www.jetlocal.co.uk/drivers/locator"

    def parse_item(self, item: Feature, location: dict, **kwargs) -> Iterable[Feature]:
        apply_category(Categories.FUEL_STATION, item)
        yield item
