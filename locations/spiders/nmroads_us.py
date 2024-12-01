from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class NmroadsUSSpider(JSONBlobSpider):
    name = "nmroads_us"
    item_attributes = {"operator": "New Mexico Department of Transportation", "operator_wikidata": "Q2250917", "extras": Categories.SURVEILLANCE_CAMERA.value}
    allowed_domains = ["servicev4.nmroads.com"]
    start_urls = ["https://servicev4.nmroads.com/RealMapWAR/GetCameraInfo"]
    locations_key = "cameraInfo"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["name"]
        item["name"] = feature["title"]
        item["extras"]["contact:webcam"] = "/".join([feature["videoServer"], feature["sdpFileHighRes"]]) + ";" + feature["snapshotFile"]
        item["extras"]["camera:type"] = "fixed"
        yield item
