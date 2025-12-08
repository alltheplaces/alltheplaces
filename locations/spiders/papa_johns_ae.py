from locations.storefinders.papa_johns_storefinder import PapaJohnsStorefinderSpider


class PapaJohnsAESpider(PapaJohnsStorefinderSpider):
    name = "papa_johns_ae"
    start_urls = ["https://order.papajohns.ae/papajohns/store-locator/?lang=en"]
    languages = ["ar", "en"]
