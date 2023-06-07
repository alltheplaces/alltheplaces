from locations.storefinders.storelocatorwidgets import StoreLocatorWidgetsSpider


class AceSafesGBSpider(StoreLocatorWidgetsSpider):
    name = "ace_safes_gb"
    item_attributes = {"brand": "Ace Safes", "brand_wikidata": "Q119157844"}
    key = "5b2c7c6dfd6937c7759a4e3330d364d7"

    def parse_item(self, item, location):
        item["city"] = item.pop("addr_full")
        yield item
