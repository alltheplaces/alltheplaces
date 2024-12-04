from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class MissouriDepartmentOfTransportationUSSpider(JSONBlobSpider):
    name = "missouri_department_of_transportation_us"
    item_attributes = {"operator": "Missouri Department of Transportation", "operator_wikidata": "Q5557977", "state": "MO"}
    allowed_domains = ["traveler.modot.org"]
    start_urls = ["https://traveler.modot.org/timconfig/feed/desktop/StreamingCams2.json"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if "/rtplive/" in feature["html"]:
            item["ref"] = feature["html"].split("/rtplive/", 1)[1].split("/playlist.m3u8", 1)[0]
        elif "/live-secure/" in feature["html"]:
            item["ref"] = feature["html"].split("/live-secure/", 1)[1].split("-LQ.stream/playlist.m3u8", 1)[0]
        item["name"] = feature["location"]
        item["lat"] = feature["y"]
        item["lon"] = feature["x"]
        apply_category(Categories.SURVEILLANCE_CAMERA.value, item)
        item["extras"]["contact:webcam"] = feature["html"]
        item["extras"]["camera:type"] = "fixed"
        yield item
