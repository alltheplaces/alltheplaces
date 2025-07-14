import json
from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class DeBerenNLSpider(JSONBlobSpider):
    name = "de_beren_nl"
    item_attributes = {"brand": "De Beren", "brand_wikidata": "Q57076079"}
    start_urls = ["https://www.beren.nl/vestigingen"]

    def extract_json(self, response: Response) -> dict | list[dict]:
        return json.loads(response.xpath("//@data-establishments").get())

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        item["website"] = "https://www.beren.nl/vestigingen/" + feature["slug"]
        apply_category(Categories.RESTAURANT, item)
        yield item
