from locations.spiders.dunkin_at import DUNKIN_SHARED_ATTRIBUTES
from locations.storefinders.storerocket import StoreRocketSpider


class DunkinCHSpider(StoreRocketSpider):
    name = "dunkin_ch"
    item_attributes = DUNKIN_SHARED_ATTRIBUTES
    storerocket_id = "Yw8l73oJvo"

    def parse_item(self, item, location):
        if item["city"].isnumeric():
            item["postcode"] = item.pop("city")
        # remove unused/non-store-specific-value fields
        item.pop("website")
        item.pop("phone")
        yield item
