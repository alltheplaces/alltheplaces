from locations.storefinders.storelocatorwidgets import StoreLocatorWidgetsSpider


class WoodmansMarketsUSSpider(StoreLocatorWidgetsSpider):
    name = "woodmans_markets_us"
    item_attributes = {"brand": "Woodman's Markets", "brand_wikidata": "Q8033073"}
    key = "60a69a063004af632806bf85f7a3b2d0"

    def parse_item(self, item, location):
        item["facebook"] = location["data"]["facebook"]
        yield item
