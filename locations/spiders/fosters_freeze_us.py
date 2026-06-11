from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class FostersFreezeUSSpider(JSONBlobSpider):
    name = "fosters_freeze_us"
    item_attributes = {"brand": "Fosters Freeze", "brand_wikidata": "Q5473851"}
    start_urls = [
        "https://www.fostersfreeze.com/api/trpc/locations.list?batch=1&input=%7B%220%22%3A%7B%22json%22%3Anull%2C%22meta%22%3A%7B%22values%22%3A%5B%22undefined%22%5D%7D%7D%7D"
    ]
    locations_key = [0, "result", "data", "json"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def pre_process_data(self, location: dict) -> None:
        location["street_address"] = location.pop("address", None)
        location.pop("name", None)

    def post_process_item(self, item: Feature, response: Response, location: dict) -> Iterable[Feature]:
        item["branch"] = location.get("label")
        if hours := location.get("hours"):
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(hours)
        apply_category(Categories.FAST_FOOD, item)
        yield item
