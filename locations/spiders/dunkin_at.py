from locations.storefinders.storerocket import StoreRocketSpider

DUNKIN_SHARED_ATTRIBUTES = {"brand": "Dunkin'", "brand_wikidata": "Q847743"}


class DunkinATSpider(StoreRocketSpider):
    name = "dunkin_at"
    item_attributes = DUNKIN_SHARED_ATTRIBUTES
    storerocket_id = "BkJ1v2z8qR"

    def parse_item(self, item, location):
        # remove unused/non-store-specific-value fields
        item.pop("website")
        yield item
