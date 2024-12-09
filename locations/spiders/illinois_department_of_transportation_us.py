from typing import Iterable

from scrapy.http import JsonRequest, Response

from locations.categories import Categories
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class IllinoisDepartmentOfTransportationUSSpider(JSONBlobSpider):
    name = "illinois_department_of_transportation_us"
    item_attributes = {
        "operator": "Illinois Department of Transportation",
        "operator_wikidata": "Q4925114",
        "state": "IL",
        "extras": Categories.SURVEILLANCE_CAMERA.value,
    }
    allowed_domains = ["travelmidwest.com"]
    start_urls = ["https://travelmidwest.com/lmiga/cameraMap.json"]
    locations_key = "features"

    def start_requests(self) -> Iterable[JsonRequest]:
        data = {"bbox": [-90, -180, 90, 180]}
        yield JsonRequest(url=self.start_urls[0], data=data, method="POST")

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if feature["properties"]["dis"]:
            # Camera disabled/unused and should be ignored.
            return
        item["ref"] = feature["properties"]["id"]
        item["name"] = feature["properties"]["locDesc"]
        item["lat"] = feature["geometry"]["coordinates"][1]
        item["lon"] = feature["geometry"]["coordinates"][0]
        if len(feature["properties"]["remUrls"]) > 1:
            item["extras"]["camera:type"] = "dome"
        else:
            item["extras"]["camera:type"] = "fixed"
        item["extras"]["contact:webcam"] = ";".join(feature["properties"]["remUrls"])
        yield item
