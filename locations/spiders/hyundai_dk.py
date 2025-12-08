from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.spiders.hyundai_kr import HYUNDAI_SHARED_ATTRIBUTES


class HyundaiDKSpider(JSONBlobSpider):
    name = "hyundai_dk"
    item_attributes = HYUNDAI_SHARED_ATTRIBUTES
    allowed_domains = ["www.hyundai.dk"]
    start_urls = [
        "https://www.hyundai.dk/api/elastic-locations/contextual?category=retail&culture=da-DK",
        "https://www.hyundai.dk/api/elastic-locations/contextual?category=workshop&culture=da-DK",
    ]
    locations_key = ["aggregations", "locations"]
    needs_json_request = True

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature.get("store_code")
        item["lat"] = feature["address"].get("lat")
        item["lon"] = feature["address"].get("lng")

        item["opening_hours"] = OpeningHours()
        for day_hours in feature.get("opening_hours"):
            days_list = OpeningHours.days_in_day_range([day_hours["open_day"].title(), day_hours["close_day"].title()])
            if not day_hours.get("open_time") or day_hours["open_time"] == "Lukket":
                item["opening_hours"].set_closed(days_list)
            else:
                item["opening_hours"].add_days_range(
                    days_list, day_hours["open_time"], day_hours["close_time"], "%H:%M"
                )

        if "category=retail" in response.url:
            apply_category(Categories.SHOP_CAR, item)
        elif "category=workshop" in response.url:
            apply_category(Categories.SHOP_CAR_REPAIR, item)

        yield item
