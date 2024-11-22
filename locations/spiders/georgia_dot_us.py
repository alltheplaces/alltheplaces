from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class GeorgiaDotUSSpider(JSONBlobSpider):
    name = "georgia_dot_us"
    item_attributes = {
        "operator": "Georgia DOT",
        "operator_wikidata": "Q944993",
        "extras": Categories.SURVEILLANCE_CAMERA.value,
    }
    start_urls = ["https://511ga.org/map/mapIcons/Cameras"]
    locations_key = "item2"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["lat"], item["lon"] = feature["location"]
        item["image"] = "https://511ga.org/map/Cctv/" + item["ref"]
        item["website"] = "https://511ga.org/map"
        item["name"] = "Traffic camera"
        item["extras"]["camera:type"] = "fixed"
        yield item
