from locations.spiders.burger_king_pr import BurgerKingPRSpider


class BurgerKingUYSpider(BurgerKingPRSpider):
    name = "burger_king_uy"
    start_urls = ["https://api-lac.menu.app/api/directory/search"]
    request_headers = {"application": "1da186d3677c7de1eed5906ac4fc2b25"}
    website_root = "https://www.burgerking.com.uy/restaurantes/"
