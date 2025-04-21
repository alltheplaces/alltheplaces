from locations.spiders.burger_king import BURGER_KING_SHARED_ATTRIBUTES
from locations.storefinders.uberall import UberallSpider


class BurgerKingBELUSpider(UberallSpider):
    name = "burger_king_be_lu"
    item_attributes = BURGER_KING_SHARED_ATTRIBUTES
    key = "PsPq35VbL5KCvUbfAeLz66TgZx2FUH"
