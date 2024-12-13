from locations.spiders.burger_king_ng import BurgerKingNGSpider


class BurgerKingCOSpider(BurgerKingNGSpider):
    name = "burger_king_co"
    start_urls = ["https://api-lac.menu.app/api/directory/search"]
    request_headers = {"application": "950709dffb805ee6cea7ae6984d4b638"}
    website_root = "https://www.bk.com.co/restaurantes/"
