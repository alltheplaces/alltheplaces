from locations.storefinders.storerocket import StoreRocketSpider


class DunkinBENLSpider(StoreRocketSpider):
    name = "dunkin_be_nl"
    item_attributes = {"brand": "Dunkin'", "brand_wikidata": "Q847743"}
    storerocket_id = "vZ4vXlw8Qd"

    def parse_item(self, item, location):
        item["country"] = item["country"].replace("Nederland", "NL")
        # remove unused/non-store-specific-value fields
        item.pop("website")
        item.pop("email")
        yield item
