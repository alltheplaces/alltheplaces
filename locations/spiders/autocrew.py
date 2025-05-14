from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class AutocrewSpider(JSONBlobSpider):
    name = "autocrew"
    item_attributes = {"brand": "AutoCrew", "brand_wikidata": "Q117794441"}
    start_urls = [
        "https://cm.emea.dxtservice.com/api/locator/findClosest?strategicClusterLevel2=117&longitude=10.176&latitude=51.068&searchRadius=100000&pageSize=200000"
    ]
    locations_key = "data"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["customerNumber"]
        item["branch"] = item.pop("name")
        apply_category(Categories.SHOP_CAR_REPAIR, item)

        item["opening_hours"] = OpeningHours()
        for day, time in feature["openingHours"].items():
            if time is None:
                continue
            for open_close_time in time:
                open_time = open_close_time["opensAt"]
                close_time = open_close_time["closesAt"]
                item["opening_hours"].add_range(day=day, open_time=open_time, close_time=close_time)

        yield item
