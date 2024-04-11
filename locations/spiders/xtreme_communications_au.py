from locations.categories import Categories, apply_category
from locations.storefinders.storelocatorwidgets import StoreLocatorWidgetsSpider


class XtremeCommunicationsAUSpider(StoreLocatorWidgetsSpider):
    name = "xtreme_communications_au"
    item_attributes = {"brand": "Xtreme Communications", "brand_wikidata": "Q116866326"}
    key = "eadfe908cc4eb517d4468cdc48c34602"

    def parse_item(self, item, location: {}, **kwargs):
        item["addr_full"] = " ".join(item["addr_full"].split())
        item.pop("website")
        apply_category(Categories.SHOP_MOBILE_PHONE, item)
        yield item
