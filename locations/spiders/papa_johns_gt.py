from locations.storefinders.papa_johns_api import PapaJohnsApiSpider


class PapaJohnsGTSpider(PapaJohnsApiSpider):
    name = "papa_johns_gt"
    start_urls = ["https://api.papajohns.com.gt/v1/stores?latitude=0&longitude=0"]
    website_base = "https://www.papajohns.com.gt/locales"
