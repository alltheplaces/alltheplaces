import json

from locations.json_blob_spider import JSONBlobSpider


class BajaFreshUSSpider(JSONBlobSpider):
    name = "baja_fresh_us"
    item_attributes = {
        "brand": "Baja Fresh",
        "brand_wikidata": "Q2880019",
    }
    start_urls = ["https://www.bajafresh.com/locator/index.php?brand=25&mode=desktop&pagesize=7000&q=55114"]

    def extract_json(self, response):
        for location_js in response.xpath("//div[starts-with(@id, 'store_')]/script/text()").getall():
            first_bracket = location_js.find(" = {")
            last_bracket = location_js.find("}", first_bracket)
            yield json.loads(location_js[first_bracket + 3 : last_bracket + 1])

    def post_process_item(self, item, response, location):
        item["street_address"] = item.pop("addr_full")
        item["branch"] = item.pop("name")
        item["extras"]["website:orders"] = location["OrderOnline"]
        item["website"] = response.urljoin(f"/stores/{location['SEOPath']}/{location['StoreId']}")
        yield item
