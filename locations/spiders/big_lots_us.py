from typing import Iterable

from scrapy.http import Response

from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class BigLotsUSSpider(JSONBlobSpider):
    name = "big_lots_us"
    item_attributes = {"brand": "Big Lots", "brand_wikidata": "Q4905973"}
    start_urls = [
        "https://core.service.elfsight.com/p/boot/?page=https%3A%2F%2Fbiglots.com%2Fstore-locator%2F&w=38636f5f-4115-4585-8c00-9e245fd92818"
    ]
    locations_key = ["data", "widgets", "38636f5f-4115-4585-8c00-9e245fd92818", "data", "settings", "locations"]
    drop_attributes = {"website", "name"}

    def pre_process_data(self, location: dict) -> None:
        location.update(location.pop("place"))

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if feature.get("photo"):
            item["image"] = feature["photo"]["url"]
        item["extras"]["ref:google:place_id"] = feature["placeId"]
        item["opening_hours"] = self.parse_opening_hours(feature)
        yield item

    def parse_opening_hours(self, location: dict) -> OpeningHours:
        oh = OpeningHours()
        for day in DAYS_FULL:
            if location["day{}Open".format(day)] is False:
                oh.set_closed(day)
                continue
            for rule in location["day{}Hours".format(day)]:
                oh.add_range(day, rule["timeRange"][0], rule["timeRange"][1])

        return oh
