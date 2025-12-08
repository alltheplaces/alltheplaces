from locations.spiders.burger_king import BURGER_KING_SHARED_ATTRIBUTES
from locations.spiders.burger_king_cz import BurgerKingCZSpider


class BurgerKingROSpider(BurgerKingCZSpider):
    name = "burger_king_ro"
    item_attributes = BURGER_KING_SHARED_ATTRIBUTES
    db = "prod_bk_ro"
    base = "https://burgerking.ro/store-locator/store/"
