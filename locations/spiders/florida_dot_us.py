from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class FloridaDotUSSpider(JSONBlobSpider):
    name = "florida_dot_us"
    item_attributes = {
        "operator": "Florida DOT",
        "operator_wikidata": "Q3074270",
        "extras": Categories.SURVEILLANCE_CAMERA.value,
    }
    start_urls = ["https://www.fl511.com/map/mapIcons/Cameras"]
    locations_key = "item2"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["lat"], item["lon"] = feature["location"]
        item["image"] = "https://www.fl511.com/map/Cctv/" + item["ref"]
        item["website"] = "https://www.fl511.com/map"
        item["name"] = "Traffic camera"
        item["extras"]["camera:type"] = "fixed"
        yield item
