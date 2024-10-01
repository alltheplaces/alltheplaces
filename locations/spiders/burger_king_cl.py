from locations.spiders.burger_king_ng import BurgerKingNGSpider


class BurgerKingCLSpider(BurgerKingNGSpider):
    name = "burger_king_cl"
    start_urls = ["https://api-lac.menu.app/api/directory/search"]
    request_headers = {"application": "509a993e252fab30945169e15e6ce1cd"}
    website_root = "https://www.burgerking.cl/locales/"
