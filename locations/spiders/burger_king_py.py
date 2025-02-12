from locations.spiders.burger_king_bs import BurgerKingBSSpider


class BurgerKingPYSpider(BurgerKingBSSpider):
    name = "burger_king_py"
    allowed_domains = ["www.burgerking.com.py"]
    host = "https://www.burgerking.com.py"
    country_code = "PY"
