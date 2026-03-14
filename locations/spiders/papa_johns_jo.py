from locations.storefinders.papa_johns_storefinder import PapaJohnsStorefinderSpider


class PapaJohnsJOSpider(PapaJohnsStorefinderSpider):
    name = "papa_johns_jo"
    start_urls = ["https://order.papajohns.jo/papajohnsjordan/store-locator/?lang=en"]
    languages = ["ar", "en"]
