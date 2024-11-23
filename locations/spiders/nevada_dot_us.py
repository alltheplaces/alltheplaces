from typing import Iterable
from urllib.parse import urlparse

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class NevadaDotUSSpider(JSONBlobSpider):
    name = "nevada_dot_us"
    item_attributes = {"operator": "Nevada DOT", "operator_wikidata": "Q886390"}
    start_urls = ["https://www.nvroads.com/map/mapIcons/Cameras"]
    locations_key = "item2"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["lat"], item["lon"] = feature["location"]
        url = urlparse(self.start_urls[0])
        item["website"] = url.scheme + "://" + url.netloc
        item["image"] = item["website"] + "/map/Cctv/" + item["ref"]
        item["name"] = "Traffic camera"
        item["extras"]["camera:type"] = "fixed"
        apply_category(Categories.SURVEILLANCE_CAMERA, item)
        yield item
