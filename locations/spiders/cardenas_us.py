from locations.storefinders.stat import StatSpider


class CardenasUSSpider(StatSpider):
    name = "cardenas_us"
    item_attributes = {"brand": "Cardenas", "brand_wikidata": "Q64149543"}
    start_urls = ["https://locations.cardenasmarkets.com/stat/api/locations/search?limit=20000"]
