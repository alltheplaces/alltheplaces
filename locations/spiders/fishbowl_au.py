from typing import Iterable

from scrapy.http import TextResponse

from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class FishbowlAUSpider(JSONBlobSpider):
    name = "fishbowl_au"
    item_attributes = {"brand": "Fishbowl", "brand_wikidata": "Q110785465"}
    start_urls = ["https://storemapper-herokuapp-com.global.ssl.fastly.net/api/users/38415-rW5LvC1Cy7c6N3Jf/stores.js"]
    custom_settings = {"ROBOTSTXT_OBEY": False}
    locations_key = "stores"

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name").replace("FISHBOWL - ", "")
        oh = OpeningHours()
        for day_time in feature.get("store_business_hours", []):
            day = DAYS_FULL[int(day_time.get("week_day")) - 1]
            open_time = day_time.get("open_time")
            close_time = day_time.get("close_time")
            oh.add_range(day=day, open_time=open_time, close_time=close_time)
        item["opening_hours"] = oh
        yield item
