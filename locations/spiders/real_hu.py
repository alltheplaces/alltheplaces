from typing import Iterable

from locations.categories import Categories, apply_category
from locations.hours import DAYS_HU
from locations.items import Feature
from locations.storefinders.maps_marker_pro import MapsMarkerProSpider


class RealHUSpider(MapsMarkerProSpider):
    name = "real_hu"
    item_attributes = {"brand": "Reál", "brand_wikidata": "Q100741414"}
    allowed_domains = ["real.hu"]
    days = DAYS_HU

    def parse_item(self, item: Feature, feature: dict, popup: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        apply_category(Categories.SHOP_CONVENIENCE, item)
        yield item
