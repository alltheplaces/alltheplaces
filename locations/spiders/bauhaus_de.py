from typing import Iterable

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.spiders.bauhaus_ch import BAUHAUS_SHARED_ATTRIBUTES
from locations.storefinders.woosmap import WoosmapSpider


class BauhausDESpider(WoosmapSpider):
    name = "bauhaus_de"
    item_attributes = BAUHAUS_SHARED_ATTRIBUTES
    key = "woos-a4988f25-802b-34df-844e-6511540dd9db"
    origin = "https://www.bauhaus.info"

    def parse_item(self, item: Feature, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        item["website"] = "https://www.bauhaus.info/fachcentren/fachcentrensuche/fc/{}".format(item["ref"])
        apply_category(Categories.SHOP_DOITYOURSELF, item)
        yield item
