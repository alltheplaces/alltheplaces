from locations.spiders.dunkin_at import DUNKIN_SHARED_ATTRIBUTES
from locations.storefinders.storerocket import StoreRocketSpider


class DunkinDESpider(StoreRocketSpider):
    name = "dunkin_de"
    item_attributes = DUNKIN_SHARED_ATTRIBUTES
    storerocket_id = "DG4gZ3yp05"

    def parse_item(self, item, location):
        # remove unused/non-store-specific-value fields
        item.pop("website")
        item.pop("phone")
        yield item
