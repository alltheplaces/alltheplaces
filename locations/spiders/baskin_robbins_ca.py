from locations.storefinders.storelocatorwidgets import StoreLocatorWidgetsSpider


class BaskinRobbinsCASpider(StoreLocatorWidgetsSpider):
    name = "baskin_robbins_ca"
    item_attributes = {"brand": "Baskin-Robbins", "brand_wikidata": "Q584601"}
    key = "4a009290a87670e408c8d77aada5c556"
