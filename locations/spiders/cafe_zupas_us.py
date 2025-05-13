from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class CafeZupasUSSpider(JSONBlobSpider):
    name = "cafe_zupas_us"
    item_attributes = {"brand": "Café Zupas", "brand_wikidata": "Q123687995"}
    allowed_domains = ["api.zupas.net"]
    start_urls = ["https://api.zupas.net/api/v1/markets/listing"]

    def extract_json(self, response: Response) -> list[dict]:
        all_features = []
        for region in response.json()["data"]["data"]:
            all_features = all_features + region["locations"]
        return all_features

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = str(feature["id"])
        item.pop("name", None)
        item["branch"] = feature["store_name"]
        item["street_address"] = item.pop("addr_full")
        item["image"] = "https://d5owcfdfld37s.cloudfront.net" + feature["image"]
        item["opening_hours"] = OpeningHours()
        if feature.get("mon_thurs_timings_open") == "Closed":
            item["opening_hours"].set_closed(["Mo", "Tu", "We", "Th"])
        elif feature.get("mon_thurs_timings_open"):
            item["opening_hours"].add_days_range(["Mo", "Tu", "We", "Th"], feature["mon_thurs_timings_open"], feature["mon_thurs_timings_close"], "%I:%M %p")
        if feature.get("fri_sat_timings_open") == "Closed":
            item["opening_hours"].set_closed(["Fr", "Sa"])
        elif feature.get("fri_sat_timings_open"):
            item["opening_hours"].add_days_range(["Fr", "Sa"], feature["fri_sat_timings_open"], feature["fri_sat_timings_close"], "%I:%M %p")
        if feature.get("sunday_timings_open") == "Closed":
            item["opening_hours"].set_closed(["Su"])
        elif feature.get("sunday_timings_open"):
            item["opening_hours"].add_days_range(["Su"], feature["sunday_timings_open"], feature["sunday_timings_close"], "%I:%M %p")
        apply_category(Categories.FAST_FOOD, item)
        item["extras"]["ref:google:place_id"] = feature["place_id"]
        yield item
