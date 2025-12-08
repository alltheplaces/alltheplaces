from locations.storefinders.papa_johns_api import PapaJohnsApiSpider


class PapaJohnsPTSpider(PapaJohnsApiSpider):
    name = "papa_johns_pt"
    start_urls = ["https://api.papajohns.pt/v1/stores?latitude=0&longitude=0"]
    website_base = "https://www.papajohns.pt/lojas"
