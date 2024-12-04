from typing import Iterable

from scrapy.http import JsonRequest, Response

from locations.categories import Categories
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class ColoradoDepartmentOfTransportationUSSpider(JSONBlobSpider):
    name = "colorado_department_of_transportation_us"
    item_attributes = {"operator": "Colorado Department of Transportation", "operator_wikidata": "Q2112717", "extras": Categories.SURVEILLANCE_CAMERA.value}
    allowed_domains = ["maps.cotrip.org"]
    start_urls = ["https://maps.cotrip.org/api/graphql"]
    locations_key = ["data", "mapFeaturesQuery", "mapFeatures"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def start_requests(self) -> Iterable[JsonRequest]:
        data = {
            "query": "query MapFeatures($input: MapFeaturesArgs!, $plowType: String) { mapFeaturesQuery(input: $input) { mapFeatures { bbox tooltip uri features { id geometry properties } ... on Sign { signDisplayType } ... on Event { priority } __typename ... on Camera { active views(limit: 5) { uri ... on CameraView { url } category } } ... on Plow { views(limit: 5, plowType: $plowType) { uri ... on PlowCameraView { url } category } } } error { message type } } }",
            "variables": {
                "input": {
                    "north": 85,
                    "east": 180,
                    "south": -85,
                    "west": -180,
                    "zoom": 15,
                    "layerSlugs": ["normalCameras"],
                    "nonClusterableUris": ["dashboard"],
                },
                "plowType": "plowCameras",
            }
        }
        yield JsonRequest(url=self.start_urls[0], data=data, method="POST")

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if feature["features"][0]["geometry"]["coordinates"][0] == 0 and feature["features"][0]["geometry"]["coordinates"][1] == 0:
            # Coordinates are missing, therefore skip this camera.
            return
        item["ref"] = feature["uri"].removeprefix("camera/")
        item["name"] = feature["tooltip"]
        item["geometry"] = feature["features"][0]["geometry"]
        if len(feature.get("views", [])) > 1:
            item["extras"]["camera:type"] = "dome"
        else:
            item["extras"]["camera:type"] = "fixed"
        image_urls = [view["url"] for view in feature.get("views", [])]
        video_urls = []
        for image_url in filter(None, image_urls):
            if image_url.startswith("https://cocam.carsprogram.org/Snapshots/"):
                stream_name = image_url.split("https://cocam.carsprogram.org/Snapshots/", 1)[1].split(".flv.png", 1)[0]
                video_urls = [f"https://publicstreamer2.cotrip.org/rtplive/{stream_name}/playlist.m3u8"]
        item["extras"]["contact:webcam"] = ";".join(filter(None, image_urls + video_urls))
        yield item
