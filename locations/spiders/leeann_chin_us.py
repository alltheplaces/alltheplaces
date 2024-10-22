from typing import Iterable

import chompjs
from scrapy.http import Response

from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class LeeannChinUSSpider(JSONBlobSpider):
    name = "leeann_chin_us"
    item_attributes = {
        "brand": "Leeann Chin",
        "brand_wikidata": "Q6515716",
    }
    start_urls = ["https://www.leeannchin.com/locations"]

    def extract_json(self, response: Response) -> list:
        return chompjs.parse_js_object(response.xpath('//script[contains(text(), "var jsonContent")]/text()').get())[
            "data"
        ]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["street"] = feature.get("address_route")
        item["addr_full"] = feature.get("location")
        yield item
