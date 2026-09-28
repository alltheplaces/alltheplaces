from typing import Iterable

from scrapy.http import JsonResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.pin_me_to import PinMeToSpider


class CarraigDonnIESpider(PinMeToSpider):
    name = "carraig_donn_ie"
    item_attributes = {"brand": "Carraig Donn"}
    id = "carraig_donn"
    key = "86f9dd039390ac824e7dc0839dcb5b97"

    def post_process_item(self, item: Feature, response: JsonResponse, location: dict, **kwargs) -> Iterable[Feature]:
        item["website"] = "https://www.carraigdonn.com/pages/store/{}".format(location["storeId"].lower())
        apply_category(Categories.SHOP_CLOTHES, item)
        yield item
