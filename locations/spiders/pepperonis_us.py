from locations.storefinders.storerocket import StoreRocketSpider


class PepperonisUSSpider(StoreRocketSpider):
    name = "pepperonis_us"
    item_attributes = {"brand": "Pepperoni's", "brand_wikidata": "Q117229592"}
    storerocket_id = "Yw8lgkZJvo"

    def parse_item(self, item, location):
        if "COMING SOON" in item["name"].upper():
            return
        yield item
