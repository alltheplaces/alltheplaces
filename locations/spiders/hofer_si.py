from typing import Iterable

from scrapy.http import TextResponse

from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class HoferSISpider(JSONBlobSpider):  # Aldi Sud
    name = "hofer_si"
    item_attributes = {"brand": "Hofer", "brand_wikidata": "Q15815751"}
    start_urls = ["https://api.hofer.si/v2/service-points?limit=1000"]
    locations_key = ["data"]

    def pre_process_data(self, feature: dict) -> None:
        feature.update(feature.pop("address"))

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["name"] = None
        item["phone"] = feature.get("publicPhoneNumber")
        yield item
