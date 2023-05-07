from locations.storefinders.storerocket import StoreRocketSpider


class DunkinDESpider(StoreRocketSpider):
    name = "dunkin_de"
    item_attributes = {"brand": "Dunkin'", "brand_wikidata": "Q847743"}
    storerocket_id = "DG4gZ3yp05"

    def parse_item(self, item, location):
        # remove unused/non-store-specific-value fields
        item.pop("website")
        item.pop("phone")
        yield item
