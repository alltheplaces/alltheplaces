from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class ClarksTWSpider(JSONBlobSpider):
    name = "clarks_tw"
    item_attributes = {"brand": "Clarks", "brand_wikidata": "Q1095857"}
    start_urls = [
        "https://webapi.91app.com/webapi/LocationV2/GetLocationList?lat=25.037929&lon=121.548818&startIndex=0&maxCount=1000&lang=zh-TW&shopId=41396"
    ]
    custom_settings = {"ROBOTSTXT_OBEY": False}
    locations_key = ["Data", "List"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["state"] = feature.get("district")
        item["extras"]["addr:district"] = feature.get("areaName")
        item["image"] = feature.get("ImageUrl")
        item["postcode"] = str(item["postcode"])
        apply_category(Categories.SHOP_SHOES, item)
        yield item
