from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class VirginiaDepartmentOfTransportationUSSpider(JSONBlobSpider):
    name = "virginia_department_of_transportation_us"
    item_attributes = {"operator": "Virginia Department of Transportation", "operator_wikidata": "Q7934247", "state": "VA", "extras": Categories.SURVEILLANCE_CAMERA.value}
    allowed_domains = ["511.vdot.virginia.gov"]
    start_urls = ["https://511.vdot.virginia.gov/services/map/layers/map/cams"]
    locations_key = "features"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if not feature["properties"]["active"]:
            return
        item["ref"] = feature["properties"]["id"]
        item["name"] = feature["properties"]["description"]
        item["extras"]["contact:webcam"] = ";".join(filter(None, [feature["properties"].get("https_url"), feature["properties"].get("rtsp_url"), feature["properties"].get("rtmp_url"), feature["properties"].get("image_url")]))
        item["extras"]["camera:type"] = "fixed"
        yield item
