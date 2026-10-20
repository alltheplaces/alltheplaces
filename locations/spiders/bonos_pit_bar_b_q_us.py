from typing import Iterable

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.storerocket import StoreRocketSpider


class BonosPitBarBQUSSpider(StoreRocketSpider):
    name = "bonos_pit_bar_b_q_us"
    item_attributes = {"brand": "Bono's Pit Bar-B-Q"}
    storerocket_id = "kDJ36e54mn"
    base_url = "https://bonosbarbq.com/locations/"

    def parse_item(self, item: Feature, location: dict) -> Iterable[Feature]:
        item["ref"] = str(item["ref"])
        item["branch"] = item.pop("name")
        item.pop("addr_full", None)
        apply_category(Categories.RESTAURANT, item)
        yield item
