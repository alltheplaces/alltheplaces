from typing import Iterable

from locations.items import Feature
from locations.storefinders.storepoint import StorepointSpider


class TazikisUSSpider(StorepointSpider):
    name = "tazikis_us"
    item_attributes = {"brand": "Taziki's Mediterranean Cafe", "brand_wikidata": "Q19849840"}
    key = "1663b8641074ad"

    def parse_item(self, item: Feature, location: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name", None)
        yield item
