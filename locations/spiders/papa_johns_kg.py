from locations.storefinders.papa_johns_storefinder import PapaJohnsStorefinderSpider


class PapaJohnsKGSpider(PapaJohnsStorefinderSpider):
    name = "papa_johns_kg"
    start_urls = ["https://order.papajohns.kg/papajohns.kg/store-locator/?lang=ru"]
    languages = ["ru", "en"]
