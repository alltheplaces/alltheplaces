from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class CaliforniaDepartmentOfTransportationCctvUSSpider(JSONBlobSpider):
    name = "california_department_of_transportation_cctv_us"
    item_attributes = {
        "operator": "California Department of Transportation",
        "operator_wikidata": "Q127743",
        "extras": Categories.SURVEILLANCE_CAMERA.value,
    }
    allowed_domains = ["cwwp2.dot.ca.gov"]
    start_urls = [
        "https://cwwp2.dot.ca.gov/data/d1/cctv/cctvStatusD01.json",
        "https://cwwp2.dot.ca.gov/data/d2/cctv/cctvStatusD02.json",
        "https://cwwp2.dot.ca.gov/data/d3/cctv/cctvStatusD03.json",
        "https://cwwp2.dot.ca.gov/data/d4/cctv/cctvStatusD04.json",
        "https://cwwp2.dot.ca.gov/data/d5/cctv/cctvStatusD05.json",
        "https://cwwp2.dot.ca.gov/data/d6/cctv/cctvStatusD06.json",
        "https://cwwp2.dot.ca.gov/data/d7/cctv/cctvStatusD07.json",
        "https://cwwp2.dot.ca.gov/data/d8/cctv/cctvStatusD08.json",
        "https://cwwp2.dot.ca.gov/data/d9/cctv/cctvStatusD09.json",
        "https://cwwp2.dot.ca.gov/data/d10/cctv/cctvStatusD10.json",
        "https://cwwp2.dot.ca.gov/data/d11/cctv/cctvStatusD11.json",
        "https://cwwp2.dot.ca.gov/data/d12/cctv/cctvStatusD12.json",
    ]

    def extract_json(self, response: Response) -> list[dict]:
        cameras_list = []
        for camera in response.json()["data"]:
            new_camera = camera["cctv"]["location"]
            new_camera["id"] = camera["cctv"]["location"]["district"] + "-" + camera["cctv"]["index"]
            new_camera["video_url"] = camera["cctv"]["imageData"]["streamingVideoURL"]
            new_camera["image_url"] = camera["cctv"]["imageData"]["static"]["currentImageURL"]
            cameras_list.append(new_camera)
        return cameras_list

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["state"] = "CA"
        item["extras"]["contact:webcam"] = ";".join(filter(None, [feature["video_url"], feature["image_url"]]))
        item["extras"]["camera:type"] = "fixed"
        yield item
