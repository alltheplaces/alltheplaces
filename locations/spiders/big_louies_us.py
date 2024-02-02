from locations.storefinders.storelocatorwidgets import StoreLocatorWidgetsSpider


class BigLouiesUSSpider(StoreLocatorWidgetsSpider):
    name = "big_louies_us"
    item_attributes = {
        "brand": "Big Louie's",
        "brand_wikidata": "Q119157997",
        "extras": {"amenity": "restaurant", "cuisine": "pizza"},
    }
    key = "178ecac2bff5d20c4041ada5f817d79e"

    def parse_item(self, item, location):
        if "Big Louies" not in location["filters"]:
            return
        item.pop("website")
        yield item
