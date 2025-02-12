from locations.storefinders.papa_johns_api import PapaJohnsApiSpider


class PapaJohnsESSpider(PapaJohnsApiSpider):
    name = "papa_johns_es"
    start_urls = ["https://api.new.papajohns.es/v1/stores?latitude=0&longitude=0"]
    website_base = "https://www.papajohns.es/locales"
