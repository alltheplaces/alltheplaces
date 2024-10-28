from locations.storefinders.papa_johns_storefinder import PapaJohnsStorefinderSpider


class PapaJohnsKESpider(PapaJohnsStorefinderSpider):
    name = "papa_johns_ke"
    start_urls = ["https://order.papajohns.ke/papajohnskenya/store-locator"]
    languages = ["en"]
