from locations.storefinders.storelocatorwidgets import StoreLocatorWidgetsSpider


class MrGattisPizzaUSSpider(StoreLocatorWidgetsSpider):
    name = "mr_gattis_pizza_us"
    item_attributes = {"brand": "Mr Gatti's Pizza", "brand_wikidata": "Q5527509"}
    key = "583c916beabda4913ceabbdd59df7689"
    drop_attributes = {"image"}

    def parse_item(self, item, location: {}, **kwargs):
        if "COMING SOON" in item["name"].upper():
            return
        yield item
