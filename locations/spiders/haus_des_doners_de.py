from typing import Iterable

from scrapy.http import TextResponse

from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class HausDesDonersDESpider(JSONBlobSpider):
    name = "haus_des_doners_de"
    start_urls = ["https://api.atlist.com/v1/map/41de535d-e707-46fa-8440-87c6fe111fb8/markers"]
    item_attributes = {"brand": "Haus des Döners", "brand_wikidata": "Q133461235"}

    def extract_json(self, response: TextResponse) -> dict:
        return super().extract_json(response)["markers"]

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        item["website"] = feature.get("buttonLink")
        if feature.get("placeId"):
            item["extras"]["ref:google:place_id"] = feature["placeId"]
        yield item
