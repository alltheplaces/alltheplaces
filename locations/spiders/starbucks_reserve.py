from chompjs import parse_js_object

from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import clean_address


class StarbucksReserveSpider(JSONBlobSpider):
    name = "starbucks_reserve"
    item_attributes = {
        "brand": "Starbucks Reserve",
        "brand_wikidata": "Q71150001",
    }
    start_urls = ["https://storage.googleapis.com/maps-solutions-x2wb8n4oyb/locator-plus/pvuv/locator-plus-config.js"]
    no_refs = True

    def extract_json(self, response):
        js_blob = "[" + response.text.split('"locations": [', 1)[1].split("],", 1)[0] + "]"
        return parse_js_object(js_blob)

    def post_process_item(self, item, response, location):
        item["addr_full"] = clean_address([location["address1"], location["address2"]])
        item["extras"]["ref:google"] = location.get("placeId")
        yield item
