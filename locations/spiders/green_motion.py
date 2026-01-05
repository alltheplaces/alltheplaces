from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_EN, DAYS_FULL, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class GreenMotionSpider(JSONBlobSpider):
    name = "green_motion"
    item_attributes = {"brand": "Green Motion", "brand_wikidata": "Q65315691"}
    start_urls = ["https://api.greenmotion.com/api/locations/?include=opening_days,country"]
    custom_settings = {"DOWNLOAD_TIMEOUT": 60}
    locations_key = "data"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        item["addr_full"] = ", ".join([feature.get(f"address_{x}") for x in range(1, 4) if feature.get(f"address_{x}")])
        item["email"] = feature.get("emails")[0]
        item["country"] = feature["country"]["data"]["iso_alpha2"]
        item["website"] = "https://greenmotion.com/locations/{}/{}".format(
            feature["country"]["data"]["slug"], feature["slug"]
        )
        self.opening_hours(feature.get("opening_days"), item)
        apply_category(Categories.CAR_RENTAL, item)
        yield item

    def opening_hours(self, times, item):
        if not times:
            return
        item["opening_hours"] = OpeningHours()
        for day in times["data"]:
            if day["name"] in DAYS_FULL:
                if day.get("is_24h"):
                    day["open"], day["close"] = ("00:00", "23:59")
                item["opening_hours"].add_range(DAYS_EN[day["name"]], day["open"], day["close"])
