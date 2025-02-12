from locations.storefinders.papa_johns_storefinder import PapaJohnsStorefinderSpider


class PapaJohnsAZSpider(PapaJohnsStorefinderSpider):
    name = "papa_johns_az"
    start_urls = ["https://order.papajohns.az/papajohns.az/store-locator/?lang=az"]
    languages = ["az", "en"]
