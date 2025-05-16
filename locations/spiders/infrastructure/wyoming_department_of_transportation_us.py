from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class WyomingDepartmentOfTransportationUSSpider(JSONBlobSpider):
    name = "wyoming_department_of_transportation_us"
    item_attributes = {
        "operator": "Wyoming Department of Transportation",
        "operator_wikidata": "Q8040331",
        "state": "WY",
        "extras": Categories.SURVEILLANCE_CAMERA.value,
    }
    allowed_domains = ["map.wyoroad.info"]
    start_urls = ["https://map.wyoroad.info/wti511map-data/webcameras_v2.json"]
    locations_key = "features"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = str(feature["properties"]["deviceid"])
        item["name"] = feature["properties"]["sitename"]
        item["extras"]["contact:webcam"] = feature["properties"]["camera_popup"]
        if len(feature["properties"].get("images")) == 1:
            item["extras"]["camera:type"] = "fixed"
        else:
            item["extras"]["camera:type"] = "dome"
        yield item
