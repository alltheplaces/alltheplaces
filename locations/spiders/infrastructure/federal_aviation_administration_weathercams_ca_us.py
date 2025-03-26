from typing import Iterable

from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class FederalAviationAdministrationWeathercamsCAUSSpider(JSONBlobSpider):
    name = "federal_aviation_administration_weathercams_ca_us"
    item_attributes = {"operator": "Federal Aviation Administration", "operator_wikidata": "Q335357"}
    allowed_domains = ["weathercams.faa.gov"]
    start_urls = ["https://weathercams.faa.gov/api/sites"]
    locations_key = "payload"

    def start_requests(self) -> Iterable[JsonRequest]:
        yield JsonRequest(url=self.start_urls[0], headers={"Referer": "https://weathercams.faa.gov"})

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        for camera_dict in feature.get("cameras", []):
            camera = item.deepcopy()
            camera["ref"] = str(camera_dict["cameraId"])
            camera["name"] = " ".join([feature["siteName"], camera_dict["cameraName"]])
            if lat := camera_dict.get("latitude"):
                if lon := camera_dict.get("longitude"):
                    camera["lat"] = lat
                    camera["lon"] = lon
            camera["website"] = "https://weathercams.faa.gov/cameras/state/US/cameraSite/{}/details/camera/{}".format(
                camera_dict["siteId"], camera_dict["cameraId"]
            )
            camera["extras"]["contact:webcam"] = camera["website"] + "/full"
            apply_category(Categories.SURVEILLANCE_CAMERA, camera)
            camera["extras"]["camera:direction"] = camera_dict.get("cameraBearing")
            yield camera
