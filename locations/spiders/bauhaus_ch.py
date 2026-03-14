from typing import Iterable

from locations.items import Feature
from locations.storefinders.woosmap import WoosmapSpider

BAUHAUS_SHARED_ATTRIBUTES = {"brand": "Bauhaus", "brand_wikidata": "Q672043"}


class BauhausCHSpider(WoosmapSpider):
    name = "bauhaus_ch"
    item_attributes = BAUHAUS_SHARED_ATTRIBUTES
    key = "woos-23dea7a7-1819-3653-a927-b29706843612"
    origin = "https://www.bauhaus.ch"

    def parse_item(self, item: Feature, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        item["website"] = "https://www.bauhaus.ch/de/s/service/fachcentren/fachcenter-{}".format(item["branch"].lower())
        yield item
