from typing import Iterable

from chompjs import parse_js_object
from scrapy.http import Response

from locations.categories import Categories
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class WashingtonStateDepartmentOfTransportationUSSpider(JSONBlobSpider):
    name = "washington_state_department_of_transportation_us"
    item_attributes = {
        "operator": "Washington State Department of Transportation",
        "operator_wikidata": "Q834834",
        "state": "WA",
        "extras": Categories.SURVEILLANCE_CAMERA.value,
    }
    allowed_domains = ["data.wsdot.wa.gov"]
    start_urls = ["https://data.wsdot.wa.gov/travelcenter/Cameras.json"]
    locations_key = ["features"]

    def extract_json(self, response: Response) -> list[dict]:
        return parse_js_object(response.text)["features"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = str(feature["attributes"]["CameraID"])
        item["name"] = feature["attributes"]["CameraTitle"]
        item["lat"] = feature["geometry"]["x"]
        item["lon"] = feature["geometry"]["y"]
        item["extras"]["contact:webcam"] = feature["attributes"]["ImageURL"]
        item["extras"]["camera:type"] = "fixed"
        yield item
