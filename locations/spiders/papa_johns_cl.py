from locations.storefinders.papa_johns_api import PapaJohnsApiSpider


class PapaJohnsCLSpider(PapaJohnsApiSpider):
    name = "papa_johns_cl"
    start_urls = ["https://api.papajohns.cl/v1/stores?latitude=0&longitude=0"]
    website_base = "https://www.papajohns.cl/locales"
