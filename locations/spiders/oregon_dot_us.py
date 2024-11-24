from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class OregonDotUSSpider(JSONBlobSpider):
    name = "oregon_dot_us"
    # TODO: some items are out of stare, discard when we get the pipeline_after_callback?
    # TODO: NSI pipeline adds an office=government tag, add operator/category to NSI
    # item_attributes = {"operator": "Oregon DOT", "operator_wikidata": "Q4413096"}
    start_urls = ["https://tripcheck.com/Scripts/map/data/cctvinventory.js"]
    locations_key = "features"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        info = feature["attributes"]
        item = DictParser.parse(info)
        item["ref"] = info["cameraId"]
        item["website"] = "https://tripcheck.com/"
        item["image"] = "https://tripcheck.com/RoadCams/cams/" + info["filename"]
        item["name"] = info["title"]
        item["extras"]["camera:type"] = "fixed"
        apply_category(Categories.SURVEILLANCE_CAMERA, item)
        yield item
