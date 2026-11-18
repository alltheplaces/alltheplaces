from typing import AsyncIterator, Iterable

from scrapy import Request
from scrapy.http import JsonRequest, TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class WilsonParkingHKSpider(JSONBlobSpider):
    name = "wilson_parking_hk"
    item_attributes = {"brand": "Wilson Parking", "brand_wikidata": "Q28448427"}
    locations_key = "data"

    async def start(self) -> AsyncIterator[JsonRequest | Request]:
        yield JsonRequest(url="https://web-api.wilsonparking.com.hk/carPark")

    def pre_process_data(self, feature: dict) -> None:
        if feature.get("coordinates"):
            feature.update(feature.pop("coordinates"))
        feature.update(feature.pop("Location"))

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        if "closed" in (item.get("name") or "").lower():
            return
        item["ref"] = feature["code"]
        item["city"] = feature["chineseDistrict"]
        item["state"] = feature["chineseRegion"]
        item["addr_full"] = feature["chineseAddress"]
        apply_category(Categories.PARKING, item)
        yield item
