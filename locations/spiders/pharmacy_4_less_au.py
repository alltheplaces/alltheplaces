from locations.storefinders.storelocatorwidgets import StoreLocatorWidgetsSpider


class Pharmacy4LessAUSpider(StoreLocatorWidgetsSpider):
    name = "pharmacy_4_less_au"
    item_attributes = {"brand": "Pharmacy 4 Less", "brand_wikidata": "Q63367608"}
    key = "6c0hBJeL5yk8cmaKJGNjTu0JhWNaMQpX"
