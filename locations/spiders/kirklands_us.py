from typing import Iterable

from scrapy.http import Response

from locations.hours import OpeningHours, day_range
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class KirklandsUSSpider(JSONBlobSpider):
    name = "kirklands_us"
    item_attributes = {
        "brand": "Kirkland's",
        "brand_wikidata": "Q6415714",
    }
    start_urls = ["https://www.kirklands.com/store-locator/stores.json"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature.get("store")
        item["street_address"] = item.pop("addr_full")
        oh = OpeningHours()
        for key, value in feature.get("hours").items():
            if "_" in key:
                start_day, end_day = key.split("_")
            else:
                start_day = end_day = key
            open_time, close_time = value.split("-")
            oh.add_days_range(
                days=day_range(start_day, end_day), open_time=open_time, close_time=close_time, time_format="%I%p"
            )
        item["opening_hours"] = oh

        yield item
