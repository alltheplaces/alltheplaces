from locations.storefinders.storerocket import StoreRocketSpider


class DunkinCHSpider(StoreRocketSpider):
    name = "dunkin_ch"
    item_attributes = {"brand": "Dunkin'", "brand_wikidata": "Q847743"}
    storerocket_id = "Yw8l73oJvo"

    def parse_item(self, item, location):
        if item["city"].isnumeric():
            item["postcode"] = item.pop("city")
        # remove unused/non-store-specific-value fields
        item.pop("website")
        item.pop("phone")
        yield item
