from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class LouisianaDotUSSpider(JSONBlobSpider):
    name = "louisiana_dot_us"
    item_attributes = {
        "operator": "Louisiana DOT",
        "operator_wikidata": "Q2400783",
        "extras": Categories.SURVEILLANCE_CAMERA.value,
    }
    start_urls = ["https://511la.org/map/mapIcons/Cameras"]
    locations_key = "item2"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["lat"], item["lon"] = feature["location"]
        item["image"] = "https://www.511la.org/map/Cctv/" + item["ref"]
        item["website"] = "https://www.511la.org/map"
        item["name"] = "Traffic camera"
        item["extras"]["camera:type"] = "fixed"
        yield item
