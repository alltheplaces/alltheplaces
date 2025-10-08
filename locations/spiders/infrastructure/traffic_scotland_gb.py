from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class TrafficScotlandGBSpider(JSONBlobSpider):
    name = "traffic_scotland_gb"
    item_attributes = {
        "operator": "Traffic Scotland",
        "operator_wikidata": "Q7834896",
        "extras": Categories.SURVEILLANCE_CAMERA.value,
    }
    allowed_domains = ["www.traffic.gov.scot"]
    start_urls = ["https://www.traffic.gov.scot/tsis/cameras"]
    locations_key = "results"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item.pop("state", None)
        item["extras"]["contact:webcam"] = "https://www.traffic.gov.scot/tsis/camerahtml?sid=" + feature["sid"]
        item["extras"]["camera:type"] = "fixed"
        for camera_id in feature["images"].split(","):
            camera = item.deepcopy()
            camera["ref"] = camera_id
            yield camera
