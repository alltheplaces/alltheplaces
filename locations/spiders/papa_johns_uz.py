from locations.storefinders.papa_johns_storefinder import PapaJohnsStorefinderSpider


class PapaJohnsUZSpider(PapaJohnsStorefinderSpider):
    name = "papa_johns_uz"
    start_urls = ["https://order.papajohns.uz/papajohns.uz/store-locator"]
    languages = ["uz", "ru", "en"]
