from typing import Iterable

import chompjs
from scrapy.http import Response

from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class NordseeSpider(JSONBlobSpider):
    name = "nordsee"
    item_attributes = {"brand": "Nordsee", "brand_wikidata": "Q74866"}
    start_urls = ["https://www.nordsee.com/de/filialen"]

    def extract_json(self, response: Response) -> list:
        return chompjs.parse_js_object(
            response.xpath('//script[contains(text(),"latitude")]/text()').get(), unicode_escape=True
        )["stores"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if item.get("state") in ["AT", "DE"]:
            item["country"] = item.pop("state")
        item["website"] = response.url
        item["phone"] = item["phone"].replace("\\/", "") if item.get("phone") else None
        yield item
