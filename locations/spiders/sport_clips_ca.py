import json

from locations.json_blob_spider import JSONBlobSpider


class SportClipsCASpider(JSONBlobSpider):
    name = "sport_clips_ca"
    item_attributes = {"brand": "Sport Clips", "brand_wikidata": "Q7579310"}
    start_urls = ["https://sportclips.ca/store-locator"]

    def extract_json(self, response):
        script = response.xpath("//script[contains(text(), 'var data = ')]/text()").get().strip().splitlines()[0]
        return json.loads(script[script.find("[") : script.rfind("]") + 1])

    def post_process_item(self, item, response, feature):
        item["branch"] = feature["SiteName"].removeprefix("Sport Clips ")
        item["street_address"] = item.pop("addr_full")
        item["website"] = item["ref"] = feature["Web"]
        yield item
