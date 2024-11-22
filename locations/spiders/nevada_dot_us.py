from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class NevadaDotUSSpider(JSONBlobSpider):
    name = "nevada_dot_us"
    item_attributes = {
        "operator": "Nevada DOT",
        "operator_wikidata": "Q886390",
        "extras": Categories.SURVEILLANCE_CAMERA.value,
    }
    start_urls = ["https://www.nvroads.com/map/mapIcons/Cameras"]
    locations_key = "item2"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["lat"], item["lon"] = feature["location"]
        item["image"] = "https://www.nvroads.com/map/Cctv/" + item["ref"]
        item["website"] = "https://www.nvroads.com/map"
        item["name"] = "Traffic camera"
        item["extras"]["camera:type"] = "fixed"
        yield item
