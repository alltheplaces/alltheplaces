import json

from locations.json_blob_spider import JSONBlobSpider


class SportClipsCASpider(JSONBlobSpider):
    name = "sport_clips_ca"
    item_attributes = {"brand": "Sport Clips", "brand_wikidata": "Q7579310"}
    start_urls = ["https://sportclips.ca/locations/"]

    def extract_json(self, response):
        script = response.xpath("//script[@id='location-map-js-extra']/text()").get()
        return json.loads(script[script.find("{") : script.rfind("}") + 1])["locations"]

    def pre_process_data(self, feature):
        feature.update(feature.pop("location", {}))

    def post_process_item(self, item, response, feature):
        item["branch"] = item.pop("name").removeprefix("Sport Clips ")
        item["ref"] = item["website"]
        yield item
