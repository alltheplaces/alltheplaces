from typing import Iterable
from urllib.parse import urlparse

from scrapy import Spider
from scrapy.http import JsonRequest, Request, Response

from locations.categories import Categories, apply_category
from locations.items import Feature


class TravelIQSpider(Spider):
    """
    Travel-IQ is a real-time road vehicle traffic management system used
    extensively in North America for providing the public with the following
    types of information:
    - Congestion
    - Variable speed limit changes
    - Roadworks
    - Traffic accidents
    - Weather information
    - Webcam feeds

    This storefinder uses an API which is exposed for and used by mobile
    applications existing for each government transportation agency. Once you
    have a Google APK, the API endpoint and API key can be extracted with:
      unzip -p "filename.apk" "assets/json/configs.json" | head -n 1 | jq -r '.web_url.production + "/api/v2/get/{feature_type}" + "?key=" + .web_api_key.production'

    Government transportation agencies typically self-host Travel-IQ software
    and provide variable types of information (for example, weather
    information may only be supplied by a subset of all users of the Travel-IQ
    software). To reveal the types of information made available by a user
    of this software, try browsing to:
      {hostname_of_api_endpoint}/developers/doc/

    This storefinder will automatically detect information provided by a user
    of this software and extract useful features.

    To use, specify:
     - 'api_endpoint': mandatory parameter
     - 'api_key': mandatory parameter
    """

    api_endpoint: str = ""
    api_key: str = ""

    def start_requests(self) -> Iterable[Request]:
        url_parts = urlparse(self.api_endpoint)
        yield Request(url=f"{url_parts.scheme}://{url_parts.netloc}/developers/doc", callback=self.parse_feature_types)

    def parse_feature_types(self, response: Response) -> Iterable[JsonRequest]:
        feature_types = response.xpath('//td[@class="api-name"]/a/text()').getall()

        if ("Cameras" in feature_types or "Traffic Cameras" in feature_types) and "Grouped Cameras" in feature_types:
            # If both "Cameras" and "Grouped Cameras" features exist, use
            # "Grouped Cameras". In this instance, "Cameras" is actually a
            # list of camera views (predefined PTZ positions where a still
            # image is periodically captured). "Grouped Cameras" is a list of
            # cameras that includes a list of camera views for each camera.
            feature_types.remove("Cameras")

        for feature_type in feature_types:
            match feature_type:
                case "Cameras" | "Traffic Cameras":
                    # The "Cameras" feature type returns a single view from
                    # fixed cameras, or multiple views from a single PTZ
                    # camera.
                    yield JsonRequest(
                        url=f"{self.api_endpoint}get/cameras?key={self.api_key}", callback=self.parse_cameras
                    )
                case "Grouped Cameras":
                    yield JsonRequest(
                        url=f"{self.api_endpoint}get/groupedcameras?key={self.api_key}", callback=self.parse_cameras
                    )
                case (
                    "Airports"
                    | "Alerts"
                    | "Alternative Fuel"
                    | "Bridges"
                    | "Events"
                    | "Express Lanes"
                    | "Ferries"
                    | "Message Signs"
                    | "Parks"
                    | "Ports Of Entry"
                    | "Rest Areas"
                    | "Road Conditions"
                    | "Truck Parking"
                    | "Variable Speed Signs"
                    | "Weather Stations"
                    | "Winter Road Conditions"
                ):
                    # Not yet implemented by this storefinder class.
                    pass
                case _:
                    # New type of feature detected.
                    self.logger.warning(
                        "New type of feature detected for Travel-IQ storefinder: {}".format(feature_type)
                    )

    def parse_cameras(self, response: Response) -> Iterable[Feature]:
        cameras = response.json()
        for camera in cameras:
            if camera.get("Status") == "Disabled":
                # Camera is disabled and should be ignored.
                continue
            properties = {
                "ref": next(ref for ref in [camera.get("SourceId"), camera.get("Id")] if ref is not None),
                "name": next(
                    name
                    for name in [
                        camera.get("Name"),
                        camera.get("Location"),
                        camera.get("Views", [{}])[0].get("Description"),
                    ]
                    if name is not None
                ),
                "lat": camera["Latitude"],
                "lon": camera["Longitude"],
            }
            apply_category(Categories.SURVEILLANCE_CAMERA, properties)
            webcam_urls = []
            if views := camera.get("Views"):
                if len([view["Status"] for view in views if view.get("Status") == "Disabled"]) == len(views):
                    # Camera is disabled and should be ignored.
                    continue
                if len(views) == 1:
                    properties["extras"]["camera:type"] = "fixed"
                else:
                    properties["extras"]["camera:type"] = "dome"
                webcam_urls += [
                    view["VideoUrl"]
                    for view in views
                    if view.get("VideoUrl") is not None and view.get("Status") != "Disabled"
                ]
                webcam_urls += [
                    view["Url"] for view in views if view.get("Url") is not None and view.get("Status") != "Disabled"
                ]
            elif fixed_image_url := camera.get("Url"):
                properties["extras"]["camera:type"] = "fixed"
                webcam_urls += [fixed_image_url]
            if video_url := camera.get("VideoUrl"):
                if "camera:type" not in properties["extras"]:
                    properties["extras"]["camera:type"] = "fixed"
                webcam_urls += [video_url]
            properties["extras"]["contact:webcam"] = ";".join(webcam_urls)
            yield Feature(**properties)
