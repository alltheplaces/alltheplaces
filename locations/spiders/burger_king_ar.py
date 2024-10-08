from locations.spiders.burger_king_ng import BurgerKingNGSpider


class BurgerKingARSpider(BurgerKingNGSpider):
    name = "burger_king_ar"
    start_urls = ["https://api-lac.menu.app/api/directory/search"]
    request_headers = {"application": "6bf38000f49df4f759e113e3ad1b8ebe"}
    website_root = "https://www.burgerking.com.ar/restaurantes/"
