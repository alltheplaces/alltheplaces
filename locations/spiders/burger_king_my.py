from locations.spiders.burger_king_sg import BurgerKingSGSpider


class BurgerKingMYSpider(BurgerKingSGSpider):
    name = "burger_king_my"
    allowed_domains = ["burgerking.com.my"]
    website_root = "https://burgerking.com.my"
