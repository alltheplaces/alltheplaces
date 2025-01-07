from typing import Iterable

from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class HimoCNSpider(JSONBlobSpider):
    name = "himo_cn"
    item_attributes = {"brand": "海马体照相馆", "brand_wikidata": "Q99284630"}
    allowed_domains = ["api-gateway.hzmantu.com"]
    start_urls = ["https://api-gateway.hzmantu.com/store/getStoreByCity"]
    locations_key = "msg"

    def start_requests(self) -> Iterable[JsonRequest]:
        data = {
            "store_type": ["blue", "gold", "family"],
            "limit": 1000,
            "type": "baseExtend",
        }
        yield JsonRequest(url=self.start_urls[0], data=data)

    def pre_process_data(self, feature: dict) -> None:
        feature.update(feature["extend"])
        del feature["extend"]
        feature["id"] = str(feature["id"])
        feature["coordinates"] = {}
        feature["coordinates"]["longitude"], feature["coordinates"]["latitude"] = feature["location"].split(",", 1)
        del feature["location"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["image"] = feature["photo"]
        apply_category(Categories.SHOP_PHOTO, item)
        yield item
