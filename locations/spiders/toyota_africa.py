from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.spiders.toyota_au import TOYOTA_SHARED_ATTRIBUTES
from locations.storefinders.uberall import UberallSpider


class ToyotaAfricaSpider(UberallSpider):
    name = "toyota_africa"
    item_attributes = TOYOTA_SHARED_ATTRIBUTES
    key = "pvr1XQQ2rjAPj8QW780wglwaNhdh2X"

    def post_process_item(self, item: Feature, response: TextResponse, location: dict) -> Iterable[Feature]:
        apply_category(Categories.SHOP_CAR, item)
        yield item
