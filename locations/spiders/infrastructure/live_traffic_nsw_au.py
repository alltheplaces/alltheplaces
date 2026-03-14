from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class LiveTrafficNswAUSpider(JSONBlobSpider):
    name = "live_traffic_nsw_au"
    item_attributes = {
        "operator": "Transport for NSW",
        "operator_wikidata": "Q7834923",
        "extras": Categories.SURVEILLANCE_CAMERA.value,
    }
    allowed_domains = ["www.livetraffic.com"]
    start_urls = ["https://www.livetraffic.com/datajson/all-feeds-web.json"]

    def pre_process_data(self, feature: dict) -> None:
        feature["id"] = feature.pop("path", feature["id"])
        feature["name"] = feature["properties"].pop("title", None)

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if not feature["eventCategory"] == "liveCams":
            return
        item["extras"]["contact:webcam"] = feature["properties"]["href"]
        item["extras"]["camera:type"] = "fixed"
        item["extras"]["camera:direction"] = feature["properties"]["direction"].replace("-", "")
        yield item
