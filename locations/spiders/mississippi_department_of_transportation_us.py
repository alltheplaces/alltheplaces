from typing import Iterable

from scrapy.http import Response, Request

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class MississippiDepartmentOfTransportationUSSpider(JSONBlobSpider):
    name = "mississippi_department_of_transportation_us"
    item_attributes = {"operator": "Mississippi Department of Transportation", "operator_wikidata": "Q5508391", "state": "MS", "extras": Categories.SURVEILLANCE_CAMERA.value}
    allowed_domains = ["api.mdottraffic.com"]
    start_urls = ["https://api.mdottraffic.com/prod/v3/data/CameraImages"]
    custom_settings = {"ROBOTSTXT_OBEY": False}
    locations_key = "value"

    def start_requests(self) -> Iterable[Request]:
        yield Request(url=self.start_urls[0], headers={"Client-Id": "01072004-0bce-4b91-b9e1-adfa6f7260d4"})

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if not feature["IsAvailable"]:
            # Camera is disabled/unavailable and should be ignored.
            return
        item["ref"] = str(feature["CameraImageId"])
        item["name"] = feature["ImageTitle"]
        if "PTZ" in feature["ImageTitle"].split():
            item["extras"]["camera:type"] = "dome"
        else:
            item["extras"]["camera:type"] = "fixed"
        item["extras"]["contact:webcam"] = ";".join([feature["StillSourceHighQuality"], feature["AddressHLSHighQuality"]])
        yield item
