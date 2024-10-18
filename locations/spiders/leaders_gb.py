import json
from typing import Iterable

from scrapy.http import Response

from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class LeadersGBSpider(JSONBlobSpider):
    name = "leaders_gb"
    item_attributes = {"brand": "Leaders", "brand_wikidata": "Q111522674"}
    start_urls = ["https://www.leaders.co.uk/contact-us"]

    def extract_json(self, response: Response) -> list:
        return json.loads(response.xpath("//@data-branches").get())

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = item["website"]
        yield item
