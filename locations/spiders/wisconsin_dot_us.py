from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class WisconsinDotUSSpider(JSONBlobSpider):
    name = "wisconsin_dot_us"
    item_attributes = {
        "operator": "Wisconsin DOT",
        "operator_wikidata": "Q8027162",
        "extras": Categories.SURVEILLANCE_CAMERA.value,
    }
    start_urls = ["https://511wi.gov/map/mapIcons/Cameras"]
    locations_key = "item2"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["lat"], item["lon"] = feature["location"]
        item["image"] = "https://511wi.gov/map/Cctv/" + item["ref"]
        item["website"] = "https://511wi.gov/"
        item["name"] = "Traffic camera"
        item["extras"]["camera:type"] = "fixed"
        yield item
