from locations.spiders.burger_king_ng import BurgerKingNGSpider


class BurgerKingBOSpider(BurgerKingNGSpider):
    name = "burger_king_bo"
    start_urls = ["https://api-lac.menu.app/api/directory/search"]
    request_headers = {"application": "67e99a607811124eda66e339c3f082d5"}
    website_root = "https://www.burgerking.com.bo/restaurantes/"
