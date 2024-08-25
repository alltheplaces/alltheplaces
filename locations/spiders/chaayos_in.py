from locations.storefinders.storerocket import StoreRocketSpider


class ChaayosINSpider(StoreRocketSpider):
    name = "chaayos_in"
    item_attributes = {"brand": "Chaayos", "brand_wikidata": "Q117235235"}
    storerocket_id = "wgprwvz4XB"

    def parse_item(self, item, location):
        # remove unused/non-store-specific-value fields
        item.pop("email")
        item.pop("phone")
        item.pop("facebook")
        item.pop("twitter")
        if "instagram" in item["extras"]:
            item["extras"].pop("instagram")
        yield item
