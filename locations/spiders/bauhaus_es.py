from typing import Iterable

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.spiders.bauhaus_ch import BAUHAUS_SHARED_ATTRIBUTES
from locations.storefinders.woosmap import WoosmapSpider


class BauhausESSpider(WoosmapSpider):
    name = "bauhaus_es"
    item_attributes = BAUHAUS_SHARED_ATTRIBUTES
    key = "woos-691aefe4-48e8-374e-9345-688f80b12146"
    origin = "https://www.bauhaus.es"

    def parse_item(self, item: Feature, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        item["website"] = "https://www.bauhaus.es/centros-bauhaus-tiendas/fc/{}".format(item["ref"])
        apply_category(Categories.SHOP_DOITYOURSELF, item)
        yield item
