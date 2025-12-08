from locations.storefinders.storerocket import StoreRocketSpider


class ChaayosINSpider(StoreRocketSpider):
    name = "chaayos_in"
    item_attributes = {"brand": "Chaayos", "brand_wikidata": "Q117235235"}
    storerocket_id = "wgprwvz4XB"

    def parse_item(self, item, location):
        # remove unused/non-store-specific-value fields
        item.pop("email", None)
        item.pop("phone", None)
        item.pop("facebook", None)
        item.pop("twitter", None)
        item["extras"].pop("instagram", None)
        yield item
