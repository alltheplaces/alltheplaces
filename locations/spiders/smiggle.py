from chompjs import parse_js_object

from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import clean_address


class SmiggleSpider(JSONBlobSpider):
    name = "smiggle"
    item_attributes = {"brand": "Smiggle", "brand_wikidata": "Q7544536"}
    start_urls = ["https://www.smiggle.co.uk/shop/en/smiggleuk/stores"]
    drop_attributes = {"facebook", "twitter"}

    def extract_json(self, response):
        js_blob = "[" + response.text.split("const storeData = [", 1)[1].split("]", 1)[0] + "]"
        return parse_js_object(js_blob)

    def post_process_item(self, item, response, location):
        item["branch"] = item.pop("name")
        item["ref"] = location["locId"]
        item["phone"].replace("  ", "")
        item["postcode"].replace("  ", "").replace(".", "")
        item["street_address"] = clean_address([location["shopAddress"], location["streetAddress"]])
        yield item
