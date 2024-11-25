from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class FiveHundredElevenNlCASpider(JSONBlobSpider):
    name = "511nl_ca"
    item_attributes = {
        "operator": "Department of Transportation and Infrastructure",
        "operator_wikidata": "Q15125415",
        "extras": Categories.SURVEILLANCE_CAMERA.value,
    }
    allowed_domains = ["511nl.ca"]
    start_urls = ["https://511nl.ca/map/mapIcons/Cameras"]
    locations_key = "item2"

    def pre_process_data(self, feature: dict) -> None:
        feature["lat"] = feature["location"][0]
        feature["lon"] = feature["location"][1]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["extras"]["contact:webcam"] = "https://511nl.ca/map/Cctv/" + item["ref"]
        item["extras"]["camera:type"] = "fixed"
        yield item
