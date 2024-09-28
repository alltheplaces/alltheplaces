from locations.spiders.burger_king_ng import BurgerKingNGSpider


class BurgerKingPRSpider(BurgerKingNGSpider):
    name = "burger_king_pr"
    start_urls = ["https://api-us.menu.app/api/directory/search"]
    request_headers = {"application": "d7f5cba9ac818278e8d167d63f9324ac"}
    website_root = "https://www.burgerkingpr.com/encuentra-tu-bk/"
