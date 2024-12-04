from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class AlabamaDepartmentOfTransportationUSSpider(JSONBlobSpider):
    name = "alabama_department_of_transportation_us"
    item_attributes = {
        "operator": "Alabama Department of Transportation",
        "operator_wikidata": "Q872788",
        "state": "AL",
        "extras": Categories.SURVEILLANCE_CAMERA.value,
    }
    allowed_domains = ["api.algotraffic.com"]
    start_urls = ["https://api.algotraffic.com/v3.0/Cameras"]
    requires_proxy = "US"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["name"] = " ".join(
            [feature["location"]["displayRouteDesignator"], feature["location"]["displayCrossStreet"]]
        )
        item["lat"] = feature["location"]["latitude"]
        item["lon"] = feature["location"]["longitude"]
        item["extras"]["contact:webcam"] = ";".join(filter(None, [feature["hlsUrl"], feature["imageUrl"]]))
        item["extras"]["camera:type"] = "fixed"
        yield item
