from locations.storefinders.uberall import UberallSpider


class HoferATSpider(UberallSpider):
    name = "hofer_at"
    item_attributes = {"brand": "Hofer", "brand_wikidata": "Q15815751"}
    key = "a7cWdBAwU03AxF6RRxwgY9Phxzh3sf"
