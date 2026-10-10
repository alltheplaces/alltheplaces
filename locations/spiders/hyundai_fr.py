from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.spiders.hyundai_kr import HYUNDAI_SHARED_ATTRIBUTES
from locations.storefinders.uberall import UberallSpider


class HyundaiFRSpider(UberallSpider):
    name = "hyundai_fr"
    item_attributes = HYUNDAI_SHARED_ATTRIBUTES
    key = "gSNTstbODTSmkLJopDa5r6buAP1PHN"

    def post_process_item(self, item: Feature, response: TextResponse, location: dict) -> Iterable[Feature]:
        apply_category(Categories.SHOP_CAR, item)
        yield item
