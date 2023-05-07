from locations.storefinders.storelocatorwidgets import StoreLocatorWidgetsSpider


class XtremeCommunicationsAUSpider(StoreLocatorWidgetsSpider):
    name = "xtreme_communications_au"
    item_attributes = {"brand": "Xtreme Communications", "brand_wikidata": "Q116866326"}
    key = "eadfe908cc4eb517d4468cdc48c34602"

    def parse_item(self, item, location: {}, **kwargs):
        item["addr_full"] = " ".join(item["addr_full"].split())
        item.pop("website")
        yield item
