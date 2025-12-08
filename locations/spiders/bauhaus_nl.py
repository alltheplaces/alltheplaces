from typing import Iterable

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.spiders.bauhaus_ch import BAUHAUS_SHARED_ATTRIBUTES
from locations.storefinders.woosmap import WoosmapSpider


class BauhausNLSpider(WoosmapSpider):
    name = "bauhaus_nl"
    item_attributes = BAUHAUS_SHARED_ATTRIBUTES
    key = "woos-e75e826a-8e6e-3172-97a0-7cf910ae7bc3"
    origin = "https://nl.bauhaus"

    def parse_item(self, item: Feature, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        item["website"] = "https://nl.bauhaus/bouwcentra/bouwcentrum-zoeken/fc/{}".format(item["ref"])
        apply_category(Categories.SHOP_DOITYOURSELF, item)
        yield item
