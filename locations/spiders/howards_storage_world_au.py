import re

from locations.storefinders.storelocatorwidgets import StoreLocatorWidgetsSpider


class HowardsStorageWorldAUSpider(StoreLocatorWidgetsSpider):
    name = "howards_storage_world_au"
    item_attributes = {"brand": "Howards Storage World", "brand_wikidata": "Q106283555"}
    key = "5ca7e612c7df4447ec76bf314efb8f52"

    def parse_item(self, item, location: {}, **kwargs):
        item["addr_full"] = re.sub(r"\s+", " ", item["addr_full"])
        yield item
