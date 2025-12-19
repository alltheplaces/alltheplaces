from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class FreshiiSpider(JSONBlobSpider):
    name = "freshii"
    item_attributes = {"brand": "Freshii", "brand_wikidata": "Q5503051"}
    start_urls = ["https://orders.freshii.com/api/locations?lang=en"]

    def pre_process_data(self, feature: dict) -> None:
        feature.update(feature.pop("GeoCoordinate"))
        feature.update(feature.pop("Address"))

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["street"] = None
        item["branch"] = item.pop("name")
        item["state"] = feature["StateProvinceCode"]
        item["phone"] = feature["PhoneNum"]

        item["opening_hours"] = OpeningHours()
        for rule in feature["AvailabilitySchedules"]:
            item["opening_hours"].add_range(rule["Day"], rule["StartTime"], rule["EndTime"], "%H:%M:%S")

        apply_category(Categories.RESTAURANT, item)

        yield item
