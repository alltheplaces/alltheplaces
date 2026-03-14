from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.spiders.burger_king import BURGER_KING_SHARED_ATTRIBUTES
from locations.storefinders.uberall import UberallSpider


class BurgerKingBELUSpider(UberallSpider):
    name = "burger_king_be_lu"
    item_attributes = BURGER_KING_SHARED_ATTRIBUTES
    key = "PsPq35VbL5KCvUbfAeLz66TgZx2FUH"

    def post_process_item(self, item: Feature, response: TextResponse, location: dict) -> Iterable[Feature]:
        apply_category(Categories.FAST_FOOD, item)
        yield item
