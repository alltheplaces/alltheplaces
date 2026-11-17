from typing import Iterable

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.spiders.kirklands_us import KirklandsUSSpider


class BedBathAndBeyondUSSpider(KirklandsUSSpider):
    """Bed Bath & Beyond's own stores, and the ones it shares with The Container Store ("1|3")."""

    name = "bed_bath_and_beyond_us"
    item_attributes = {"brand": "Bed Bath & Beyond", "brand_wikidata": "Q813782"}
    brand_ids = {"1"}

    def post_process_item(self, item: Feature, store: dict) -> Iterable[Feature]:
        item["branch"] = item["branch"].removeprefix("Bed Bath & Beyond / The Container Store - ")
        apply_category(Categories.SHOP_HOUSEWARE, item)
        yield item
