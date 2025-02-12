from locations.storefinders.papa_johns_storefinder import PapaJohnsStorefinderSpider


class PapaJohnsSASpider(PapaJohnsStorefinderSpider):
    name = "papa_johns_sa"
    start_urls = ["https://order.papajohns.sa/papajohnsksa/store-locator/?lang=en"]
    languages = ["ar", "en"]
