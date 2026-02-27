from typing import Iterable

from scrapy.http import Response

from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class ChemistWarehouseNZSpider(JSONBlobSpider):
    name = "chemist_warehouse_nz"
    item_attributes = {"brand": "Chemist Warehouse", "brand_wikidata": "Q48782120"}
    start_urls = ["https://www.chemistwarehouse.co.nz/webapi/store/store-locator?BusinessGroupId=4"]
    needs_json_request = True

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("Chemist Warehouse")
        item["lat"], item["lon"] = feature["GeoPoint"]["Latitude"], feature["GeoPoint"]["Longitude"]
        item["opening_hours"] = OpeningHours()
        for rules in feature["OpenHours"]:
            item["opening_hours"].add_range(rules["WeekDay"], rules["OpenTime"], rules["CloseTime"], "%H:%M:%S")
        yield item
