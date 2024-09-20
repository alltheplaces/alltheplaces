from locations.categories import Categories, apply_category
from locations.json_blob_spider import JSONBlobSpider


class OmnivaSpider(JSONBlobSpider):
    name = "omniva"
    item_attributes = {"brand": "Omniva", "brand_wikidata": "Q282457"}
    CAT_TYPE = {
        "0": Categories.PARCEL_LOCKER,
        "1": Categories.POST_OFFICE,
    }
    start_urls = ["https://www.omniva.lt/locations.json"]
    no_refs = True

    def post_process_item(self, item, response, location):
        item["country"] = location["A0_NAME"]
        item["lat"] = location["Y_COORDINATE"]
        item["lon"] = location["X_COORDINATE"]
        if category := self.CAT_TYPE.get(location["TYPE"]):
            apply_category(category, item)
            yield item
        else:
            self.logger.error("unknown category type: " + location["TYPE"])
