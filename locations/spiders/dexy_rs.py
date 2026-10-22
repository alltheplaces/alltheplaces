from typing import Iterable

from scrapy.http import TextResponse

from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class DexyRSSpider(JSONBlobSpider):
    name = "dexy_rs"
    item_attributes = {"brand": "Dexy Co", "brand_wikidata": "Q97192674"}
    start_urls = ["https://www.dexy.co.rs/listing-radnji?type=json&ver=1"]
    locations_key = "stores"

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item.pop("name", None)
        item["street_address"] = item.pop("street", None)
        item["lat"] = feature["coordinatesGoogleMapWidth"] or None
        item["lon"] = feature["coordinatesGoogleMapHeight"] or None
        item["website"] = feature["f_permalink"]

        item["opening_hours"] = OpeningHours()
        for day, times in (feature.get("f_workingHoursObject") or {}).items():
            if times.get("from") and times.get("to"):
                item["opening_hours"].add_range(day, times["from"], times["to"], time_format="%H:%M:%S")

        yield item
