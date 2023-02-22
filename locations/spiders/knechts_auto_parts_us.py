from locations.storefinders.storelocatorwidgets import StoreLocatorWidgetsSpider


class KnechtsAutoPartsUSSpider(StoreLocatorWidgetsSpider):
    name = "knechts_auto_parts_us"
    item_attributes = {"brand": "Knecht's Auto Parts", "brand_wikidata": "Q116866978"}
    key = "8093259cc75e262129501c9797799e8d"

    def parse_item(self, item, location: {}, **kwargs):
        item["addr_full"] = " ".join(item["addr_full"].split())
        item.pop("website")
        yield item
