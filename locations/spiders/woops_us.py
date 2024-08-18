from typing import Any

import chompjs

from locations.json_blob_spider import JSONBlobSpider


class WoopsUSSpider(JSONBlobSpider):
    name = "woops_us"
    item_attributes = {
        "brand_wikidata": "Q110474786",
        "brand": "Woops!",
    }
    allowed_domains = [
        "bywoops.com",
    ]
    start_urls = ["https://bywoops.com/locations-list/"]

    def extract_json(self, response):
        return chompjs.parse_js_object(response.xpath("//div/@data-positions").get())

    def pre_process_data(self, location) -> Any:
        location["id"] = location["postName"]
        location["website"] = "https://bywoops.com/locations/" + location["postName"] + "/"
