from chompjs import parse_js_object

from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import clean_address

class ScribblerGBSpider(JSONBlobSpider):
    name = "scribbler_gb"
    item_attributes = {"brand": "Scribbler", "brand_wikidata": "Q28457455"}
    allowed_domains = ["storage.googleapis.com"]
    start_urls = ["https://storage.googleapis.com/maps-solutions-snuj0y4vpu/locator-plus/lhic/locator-plus-config.js"]
    no_refs = True

    def extract_json(self, response):
        js_blob = "[" + response.text.split('"locations": [', 1)[1].split("],", 1)[0] + "]"
        return parse_js_object(js_blob)

    def post_process_item(self, item, response, location):
        item["addr_full"] = clean_address([location["address1"], location["address2"]])
        item["extras"]["ref:google"] = location.get("placeId")
        item["lat"]=location["coords"]["lat"]
        item["lon"]=location["coords"]["lng"]
        yield item
