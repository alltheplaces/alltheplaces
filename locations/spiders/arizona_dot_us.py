from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class ArizonaDotUSSpider(JSONBlobSpider):
    name = "arizona_dot_us"
    item_attributes = {
        "operator": "Arizona DOT",
        "operator_wikidata": "Q807704",
        "extras": Categories.SURVEILLANCE_CAMERA.value,
    }
    start_urls = ["https://www.az511.com/map/mapIcons/Cameras"]
    locations_key = "item2"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["lat"], item["lon"] = feature["location"]
        item["image"] = "https://www.az511.com/map/Cctv/" + item["ref"]
        item["website"] = "https://www.az511.com/"
        item["name"] = "Traffic camera"
        item["extras"]["camera:type"] = "fixed"
        yield item
