from locations.storefinders.closeby import ClosebySpider


class SpeedyStopUSSpider(ClosebySpider):
    name = "speedy_stop_us"
    item_attributes = {"brand": "Speedy Stop", "brand_wikidata": "Q123419843"}
    api_key = "c9271c9124f5bdd13fc0258d3453ed6f"
