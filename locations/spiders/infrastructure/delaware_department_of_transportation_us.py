from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class DelawareDepartmentOfTransportationUSSpider(JSONBlobSpider):
    name = "delaware_department_of_transportation_us"
    item_attributes = {
        "operator": "Delaware Department of Transportation",
        "operator_wikidata": "Q3297972",
        "state": "DE",
        "extras": Categories.SURVEILLANCE_CAMERA.value,
    }
    allowed_domains = ["tmc.deldot.gov"]
    start_urls = ["https://tmc.deldot.gov/json/videocamera.json"]
    locations_key = "videoCameras"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if not feature["enabled"] or feature["status"] != "Active":
            # Camera is disabled/removed and should be ignored.
            return
        item["extras"]["contact:webcam"] = ";".join(
            filter(None, [feature["urls"].get("rtmp"), feature["urls"].get("rtsp"), feature["urls"].get("m3u8s")])
        )
        item["extras"]["camera:type"] = "fixed"
        yield item
