from locations.spiders.burger_king_bs import BurgerKingBSSpider


class BurgerKingDOSpider(BurgerKingBSSpider):
    name = "burger_king_do"
    allowed_domains = ["www.burgerking.com.do"]
    host = "https://www.burgerking.com.do"
    country_code = "DO"
