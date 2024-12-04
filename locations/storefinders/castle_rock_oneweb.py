from typing import Iterable

from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class CastleRockOneWebSpider(JSONBlobSpider):
    """
    Castle Rock OneWeb is an Advanced Traveler Information System (ATIS)
    used for real time traffic monitoring and management. The following types
    of information are made available through public traffic information
    websites:
     - Road incident (accident) locations
     - Road construction works locations
     - Traffic camera locations and feeds
     - Snow plow locations and statuses

    To use, specify:
      - 'api_endpoint': mandatory parameter, the URL of the API endpoint
        ending '/api/graphql'.
      - 'video_url_template': mandatory parameter, the formatter string of
        URLs of traffic camera video streams. Use "{}" as the variable
        for the name of the feed (filename of the .m3u8 file).
    """

    api_endpoint: str = None
    locations_key: list[str] = ["data", "mapFeaturesQuery", "mapFeatures"]
    video_url_template: str = None

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
            },
        }
        yield JsonRequest(url=self.api_endpoint, data=data, method="POST")

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if (
            feature["features"][0]["geometry"]["coordinates"][0] == 0
            and feature["features"][0]["geometry"]["coordinates"][1] == 0
        ):
            # Coordinates are missing, therefore skip this camera.
            return
        item["ref"] = feature["uri"].removeprefix("camera/")
        item["name"] = feature["tooltip"]
        item["geometry"] = feature["features"][0]["geometry"]
        apply_category(Categories.SURVEILLANCE_CAMERA, item)
        if len(feature.get("views", [])) > 1:
            item["extras"]["camera:type"] = "dome"
        else:
            item["extras"]["camera:type"] = "fixed"
        image_urls = [view["url"] for view in feature.get("views", [])]
        video_urls = []
        for image_url in filter(None, image_urls):
            stream_name = image_url.split("/")[-1].split(".flv.png", 1)[0]
            video_urls = [self.video_url_template.format(stream_name)]
        item["extras"]["contact:webcam"] = ";".join(filter(None, image_urls + video_urls))
        yield item
