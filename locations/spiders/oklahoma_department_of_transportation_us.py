from typing import Iterable

from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class OklahomaDepartmentOfTransportationUSSpider(JSONBlobSpider):
    name = "oklahoma_department_of_transportation_us"
    item_attributes = {"operator": "Oklahoma Department of Transportation", "operator_wikidata": "Q2171739"}
    allowed_domains = ["oktraffic.org"]
    start_urls = ["https://oktraffic.org/api/CameraPoles"]

    def start_requests(self) -> Iterable[JsonRequest]:
        yield JsonRequest(self.start_urls[0], headers={"filter": '{"include":[{"relation":"mapCameras","scope":{"include":"streamDictionary","where":{"status":{"neq":"Out Of Service"},"type":"Web","blockAtis":{"neq":"1"}}}},{"relation":"cameraLocationLinks","scope":{"include":["linkedCameraPole","cameraPole"]}}]}'})

    def parse(self, response: Response) -> Iterable[Feature]:
        for camera_pole in response.json():
            for camera in camera_pole.get("mapCameras", []):
                properties = {
                    "ref": camera["id"],
                    "name": camera["streamDictionary"]["streamName"],
                    "lat": camera["latitude"],
                    "lon": camera["longitude"],
                }
                apply_category(Categories.SURVEILLANCE_CAMERA, properties)
                properties["extras"]["contact:webcam"] = camera["streamDictionary"]["streamSrc"],
                properties["extras"]["camera:type"] = "fixed"
                yield Feature(**properties)
