from typing import Iterable

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.spiders.bauhaus_ch import BAUHAUS_SHARED_ATTRIBUTES
from locations.storefinders.woosmap import WoosmapSpider


class BauhausATSpider(WoosmapSpider):
    name = "bauhaus_at"
    item_attributes = BAUHAUS_SHARED_ATTRIBUTES
    key = "woos-70aef73b-48e0-31d3-8778-e2a3244627f4"
    origin = "https://www.bauhaus.at"

    def parse_item(self, item: Feature, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        item["website"] = "https://www.bauhaus.at/fachcentren/fachcentrensuche/fc/{}".format(item["ref"])
        apply_category(Categories.SHOP_DOITYOURSELF, item)
        yield item
