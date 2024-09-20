from locations.storefinders.storepoint import StorepointSpider


class PowerFashionZASpider(StorepointSpider):
    name = "power_fashion_za"
    key = "162e1380619248"
    item_attributes = {"brand": "Power", "brand_wikidata": "Q118185713"}
