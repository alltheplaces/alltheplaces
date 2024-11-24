from typing import Iterable

import scrapy
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class MichiganDotUSSpider(JSONBlobSpider):
    name = "michigan_dot_us"
    item_attributes = {"operator": "Michigan DOT", "operator_wikidata": "Q2350930"}
    start_urls = ["https://mdotjboss.state.mi.us/MiDrive/camera/AllForMap/"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        camera_info = f"https://mdotjboss.state.mi.us/MiDrive/camera/getCameraInformation/{feature['id']}"
        yield scrapy.Request(url=camera_info, callback=self.camera_info)

    def camera_info(self, response):
        camera_info = response.json()
        item = DictParser.parse(camera_info)
        apply_category(Categories.SURVEILLANCE_CAMERA, item)
        item["website"] = "https://mdotjboss.state.mi.us/MiDrive/map"
        item["image"] = camera_info["link"]
        yield item
