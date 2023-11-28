from locations.storefinders.storerocket import StoreRocketSpider


class RibCribUSSpider(StoreRocketSpider):
    name = "ribcrib_us"
    item_attributes = {"brand": "RibCrib", "brand_wikidata": "Q7322197"}
    storerocket_id = "6wgpr528XB"

    def parse_item(self, item, location):
        item["website"] = "https://ribcrib.com/locations/?location=" + location.get("slug")
        yield item
