import chompjs

from locations.categories import Categories, apply_category
from locations.json_blob_spider import JSONBlobSpider


class UpimSpider(JSONBlobSpider):
    name = "upim"
    UPIM = {"brand": "Upim", "brand_wikidata": "Q1414836"}
    BLUKIDS = {"brand": "Blukids", "name": "Blukids"}
    start_urls = ["https://stores.upim.com/js_db/locations-1.js"]

    def extract_json(self, response):
        return chompjs.parse_js_object(response.text)

    def post_process_item(self, item, response, location):
        item["street_address"] = location["a1"]
        item["state"] = location["prov"]
        item["postcode"] = location["cap"]
        item["country"] = location["country_tag"]
        item["website"] = location["l"]

        if item["name"].upper().startswith("UPIM"):
            item["branch"] = item.pop("name").split(" ", 1)[1]
            item.update(self.UPIM)
        elif item["name"].upper().startswith("BLUKIDS"):
            item["branch"] = item.pop("name").split(" ", 1)[1].removesuffix(" Bk")
            item.update(self.BLUKIDS)
            apply_category(Categories.SHOP_CLOTHES, item)

        yield item
