import re
from typing import Iterable

from scrapy.http import JsonRequest, TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class BoatingVicSlipwaysWebcamsAUSpider(ArcGISFeatureServerSpider):
    name = "boating_vic_slipways_webcams_au"
    host = "services8.arcgis.com"
    context_path = "vGm0HIi6EkFEEDDl/ArcGIS"
    service_id = "BVRamps"
    layer_id = "0"

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[JsonRequest]:
        item["ref"] = feature["RampExID"]
        item["name"] = feature["RampName"]
        item["website"] = "https://www.boating.vic.gov.au/ramps/" + feature["Location_ID"]
        yield JsonRequest(
            url="https://www.boating.vic.gov.au/api/v1/facilityDetails/" + feature["Location_ID"],
            meta={"item": item},
            callback=self.parse_facility_details,
        )

    def parse_facility_details(self, response: TextResponse) -> Iterable[Feature | JsonRequest]:
        facility = response.json()[0]

        if facility["isDeleted"]:
            return

        facility_item = response.meta["item"]
        if operator_name := facility.get("facilityManagerName"):
            facility_item["operator"] = operator_name

        for ramp in facility["Ramps"]:
            ramp_item = facility_item.deepcopy()
            ramp_item["ref"] = ramp["rampId"]
            ramp_item["name"] = ramp["rampName"]
            apply_category(Categories.LEISURE_SLIPWAY, ramp_item)
            match ramp.get("rampConstruction"):
                case "Concrete/Asphalt":
                    ramp_item["extras"]["surface"] = "concrete;asphalt"
                case "Gravel":
                    ramp_item["extras"]["surface"] = "gravel"
                case "Other" | None:
                    pass
                case "Sand / Beach Launch":
                    ramp_item["extras"]["surface"] = "sand"
                case "Timber":
                    ramp_item["extras"]["surface"] = "timber"
                case _:
                    self.logger.warning("Unknown ramp surface: {}".format(ramp["rampConstruction"]))
            yield ramp_item

        if facility["atleastOneActiveCamera"] or facility["atleastOneActiveCarparkCamera"]:
            yield JsonRequest(
                url="https://www.boating.vic.gov.au/api/v1/cameraImages/" + facility["facilityId"],
                meta={"item": facility_item},
                callback=self.parse_webcams,
            )

    def parse_webcams(self, response: TextResponse) -> Iterable[Feature]:
        # Note: webcam image URLs contain a timestamp and digital signature
        # (meaning they expire) and a request to the cameraImages API needs to
        # be made to generate a time-limited image URL on demand. The webcam
        # URL is therefore set to be the main website for the facility which
        # makes the API requests necessary to display all the latest webcam
        # images for the facility.
        facility_item = response.meta["item"]
        for camera in response.json():
            if not camera.get("cameraliveimage"):
                continue
            camera_item = facility_item.deepcopy()
            camera_item["operator"] = "Safe Transport Victoria"
            camera_item["operator_wikidata"] = "Q137715159"
            if m := re.search(r"\/(?:live|set)\/([^.]+)\.", camera["cameraliveimage"]):
                camera_item["ref"] = m.group(1)
            else:
                self.logger.warning(
                    "Could not locate camera ID in live image URL: {}".format(camera["cameraliveimage"])
                )
                continue
            camera_item["extras"]["contact:webcam"] = facility_item["website"]
            apply_category(Categories.SURVEILLANCE_CAMERA, camera_item)
            yield camera_item
