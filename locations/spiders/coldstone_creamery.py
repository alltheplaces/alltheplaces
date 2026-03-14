import json

from locations.json_blob_spider import JSONBlobSpider


class ColdstoneCreamerySpider(JSONBlobSpider):
    name = "coldstone_creamery"
    item_attributes = {"brand": "Cold Stone Creamery", "brand_wikidata": "Q1094923"}
    start_urls = ["https://www.coldstonecreamery.com/locator/index.php?brand=14&mode=desktop&pagesize=7000&q=55114"]

    def extract_json(self, response):
        for location_js in response.xpath('//div[@class="listing"]/script/text()').getall():
            first_bracket = location_js.find("{")
            last_bracket = location_js.rfind("}")
            yield json.loads(location_js[first_bracket : last_bracket + 1])

    def post_process_item(self, item, response, location):
        item["street_address"] = item.pop("addr_full")
        item["branch"] = item.pop("name")
        item["extras"]["website:orders"] = location["OrderOnline"]
        item["website"] = response.urljoin(f"/stores/{location['StoreId']}")
        yield item
