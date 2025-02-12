from locations.storefinders.papa_johns_api import PapaJohnsApiSpider


class PapaJohnsPASpider(PapaJohnsApiSpider):
    name = "papa_johns_pa"
    start_urls = ["https://api.papajohns.com.pa/v1/stores?latitude=0&longitude=0"]
    website_base = "https://www.papajohns.com.pa/locales"
