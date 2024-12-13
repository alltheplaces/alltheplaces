from locations.spiders.burger_king_bs import BurgerKingBSSpider


class BurgerKingFJSpider(BurgerKingBSSpider):
    name = "burger_king_fj"
    allowed_domains = ["www.burgerkingfiji.com"]
    host = "https://www.burgerkingfiji.com"
    country_code = "FJ"
