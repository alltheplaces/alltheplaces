from locations.storefinders.papa_johns_storefinder import PapaJohnsStorefinderSpider


class PapaJohnsKZSpider(PapaJohnsStorefinderSpider):
    name = "papa_johns_kz"
    start_urls = ["https://order.papajohns.kz/papajohnskazakhstan/store-locator/?lang=kz"]
    languages = ["kk", "ru", "en"]
