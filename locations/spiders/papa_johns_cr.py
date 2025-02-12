from locations.storefinders.papa_johns_api import PapaJohnsApiSpider


class PapaJohnsCRSpider(PapaJohnsApiSpider):
    name = "papa_johns_cr"
    start_urls = ["https://api.papajohns.cr/v1/stores?latitude=0&longitude=0"]
    website_base = "https://www.papajohns.cr/locales"
