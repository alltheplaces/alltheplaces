from locations.spiders.dunkin_at import DUNKIN_SHARED_ATTRIBUTES
from locations.storefinders.storerocket import StoreRocketSpider


class DunkinBENLSpider(StoreRocketSpider):
    name = "dunkin_be_nl"
    item_attributes = DUNKIN_SHARED_ATTRIBUTES
    storerocket_id = "vZ4vXlw8Qd"

    def parse_item(self, item, location):
        item["country"] = item["country"].replace("Nederland", "NL")
        # remove unused/non-store-specific-value fields
        item.pop("website")
        item.pop("email")
        yield item
