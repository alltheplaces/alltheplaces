from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class OhioDotUSSpider(JSONBlobSpider):
    name = "ohio_dot_us"
    item_attributes = {"operator": "Ohio DOT", "operator_wikidata": "Q4955209"}
    start_urls = ["https://api.ohgo.com/roadmarkers/TrafficSpeedAndAlertMarkers"]
    locations_key = "CameraMarkers"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["name"] = feature["Location"]
        item["website"] = "https://www.ohgo.com/"
        item["image"] = feature["Cameras"][0]["SmallURL"]
        item["extras"]["camera:type"] = "fixed"
        apply_category(Categories.SURVEILLANCE_CAMERA, item)
        yield item
