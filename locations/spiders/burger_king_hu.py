from locations.spiders.burger_king_bs import BurgerKingBSSpider


class BurgerKingHUSpider(BurgerKingBSSpider):
    name = "burger_king_hu"
    allowed_domains = ["burgerking.hu"]
    host = "https://burgerking.hu"
    country_code = "HU"
