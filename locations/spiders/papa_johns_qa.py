from locations.storefinders.papa_johns_storefinder import PapaJohnsStorefinderSpider


class PapaJohnsQASpider(PapaJohnsStorefinderSpider):
    name = "papa_johns_qa"
    start_urls = ["https://order.papajohns.qa/papajohnsqatar/store-locator/?lang=en"]
    languages = ["ar", "en"]
