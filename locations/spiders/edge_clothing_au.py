from locations.storefinders.storelocatorwidgets import StoreLocatorWidgetsSpider


class EdgeClothingAUSpider(StoreLocatorWidgetsSpider):
    name = "edge_clothing_au"
    item_attributes = {"brand": "Edge Clothing", "brand_wikidata": "Q117847766"}
    key = "2483c75758e370cbeab6e15e7820d658"
