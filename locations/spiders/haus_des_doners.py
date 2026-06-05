from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class HausDesDonersSpider(JSONBlobSpider):
    name = "haus_des_doners"
    start_urls = ["https://api.atlist.com/v1/map/41de535d-e707-46fa-8440-87c6fe111fb8/markers"]
    item_attributes = {"brand": "Haus des Döners", "brand_wikidata": "Q133461235"}
    locations_key = "markers"

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["branch"] = (item.pop("name") or "").strip()
        if " - " in item["branch"]:
            item["ref"], item["branch"] = item["branch"].split(" - ")
        elif " " in item["branch"]:
            item["branch"], item["ref"] = item["branch"].rsplit(" ", 1)

        item["website"] = feature.get("buttonLink")
        if feature.get("placeId"):
            item["extras"]["ref:google:place_id"] = feature["placeId"]

        apply_category(Categories.FAST_FOOD, item)

        yield item
