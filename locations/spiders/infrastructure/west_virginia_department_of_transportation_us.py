from typing import Iterable

from chompjs import parse_js_object
from scrapy.http import Response

from locations.categories import Categories
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class WestVirginiaDepartmentOfTransportationUSSpider(JSONBlobSpider):
    name = "west_virginia_department_of_transportation_us"
    item_attributes = {
        "operator": "West Virginia Department of Transportation",
        "operator_wikidata": "Q7986842",
        "state": "WV",
        "extras": Categories.SURVEILLANCE_CAMERA.value,
    }
    allowed_domains = ["wv511.org"]
    start_urls = ["https://wv511.org/wsvc/gmap.asmx/buildCamerasJSONjs"]

    def extract_json(self, response: Response) -> list[dict]:
        cameras = "[{" + response.text.split('"cams": [{', 1)[1].split("}]", 1)[0] + "}]"
        return parse_js_object(cameras)

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["md5"]
        item["name"] = feature["title"]
        item["lat"] = feature["start_lat"]
        item["lon"] = feature["start_lng"]
        item["extras"]["camera:type"] = "fixed"
        item["extras"]["contact:webcam"] = "https://sfs1.roadsummary.com/rtplive/{}/playlist.m3u8".format(item["ref"])
        yield item
