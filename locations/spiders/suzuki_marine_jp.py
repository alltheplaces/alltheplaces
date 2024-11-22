from typing import Iterable

from scrapy.http import Response

from locations.categories import apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider

SUZUKI_MARINE_SHARED_ATTRIBUTES = {"brand": "Suzuki", "brand_wikidata": "Q181642"}


class SuzukiMarineJPSpider(JSONBlobSpider):
    name = "suzuki_marine_jp"
    item_attributes = SUZUKI_MARINE_SHARED_ATTRIBUTES
    allowed_domains = ["www1.suzuki.co.jp"]
    start_urls = ["https://www1.suzuki.co.jp/marine/dealer/data/data.php"]
    locations_key = "items"

    def pre_process_data(self, feature: dict) -> None:
        feature["id"] = feature.pop("cd", None)
        if not feature.get("url") and feature["id"]:
            feature["website"] = "https://www1.suzuki.co.jp/marine/dealer/detail/?cd=" + feature["id"]

        # TODO: parse complex opening hours
        # Example: 【4-9月】9:00～18:00\u3000【10-3月】9:00～17:00
        #            ^April-September: 09:00-18:00
        #                              ^erronous unescaped Unicode character
        #                                    ^October-March: 09:00-17:00
        #          火曜日または水曜日
        #          ^closed Tuesday and Wednesday each week

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if not item["ref"]:
            return  # Blank location returned - ignore it.
        apply_category({"boat:parts": "yes"}, item)
        yield item
