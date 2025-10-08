from typing import Iterable

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.spiders.bauhaus_ch import BAUHAUS_SHARED_ATTRIBUTES
from locations.storefinders.woosmap import WoosmapSpider


class BauhausHRSpider(WoosmapSpider):
    name = "bauhaus_hr"
    item_attributes = BAUHAUS_SHARED_ATTRIBUTES
    key = "woos-5650045b-109f-333d-ab46-ed3b749ad9e3"
    origin = "https://www.bauhaus.hr"

    def parse_item(self, item: Feature, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        item["website"] = "https://www.bauhaus.hr/prodajni-centri/pretraga/fc/{}".format(item["ref"])
        apply_category(Categories.SHOP_DOITYOURSELF, item)
        yield item
