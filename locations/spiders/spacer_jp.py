from typing import Iterable

from scrapy.http import Response

from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class SpacerJPSpider(JSONBlobSpider):
    name = "spacer_jp"
    item_attributes = {"brand": "SPACER"}
    custom_settings = {"ROBOTSTXT_OBEY": False}
    start_urls = [
        "https://locker-c5f2c.firebaseio.com/spacersLocations.json?auth=AIzaSyCt9HAVOsFXvd0bXRlFcUE093mR9T82tmk"
    ]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if feature.get("isHiddenMap"):
            return
        if not feature.get("lat") or not feature.get("lng"):
            return

        item["branch"] = item.pop("name", None)
        item["country"] = "JP"
        item["extras"]["amenity"] = "left_luggage"

        oh = OpeningHours()
        open_time = feature.get("open")
        close_time = feature.get("close")
        if open_time and close_time:
            oh.add_days_range(DAYS, open_time, close_time)
        else:
            oh.add_days_range(DAYS, "00:00", "23:59")
        item["opening_hours"] = oh

        yield item
