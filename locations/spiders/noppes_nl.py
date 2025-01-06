from typing import Iterable

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.store_locator_plus_self import StoreLocatorPlusSelfSpider


class NoppesNLSpider(StoreLocatorPlusSelfSpider):
    name = "noppes_nl"
    item_attributes = {"brand": "Noppes", "brand_wikidata": "Q100890364"}
    allowed_domains = ["www.noppeskringloopwinkel.nl"]
    iseadgg_countries_list = ["NL"]
    search_radius = 200
    max_results = 1000

    def parse_item(self, item: Feature, location: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("Kledingbak ")
        apply_category(Categories.SHOP_SECOND_HAND, item)
        yield item
