from locations.spiders.burger_king_ng import BurgerKingNGSpider


class BurgerKingALSpider(BurgerKingNGSpider):
    name = "burger_king_al"
    start_urls = ["https://api.menu.app/api/directory/search"]
    request_headers = {"application": "d64f82486485860b1b541fb85849d719"}
    website_root = "https://www.burgerking.al/restaurants/"
