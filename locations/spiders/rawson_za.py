from chompjs import parse_js_object

from locations.json_blob_spider import JSONBlobSpider


class RawsonZASpider(JSONBlobSpider):
    name = "rawson_za"
    item_attributes = {"brand": "Rawson Property Group", "brand_wikidata": "Q130379454"}
    start_urls = ["https://rawson.co.za/offices"]

    def extract_json(self, response):
        return parse_js_object(response.xpath(".//find-office-map").get())

    def post_process_item(self, item, response, location):
        item["street_address"] = item.pop("addr_full")
        yield item
