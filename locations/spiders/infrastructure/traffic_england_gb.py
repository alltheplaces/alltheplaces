import re
from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class TrafficEnglandGBSpider(JSONBlobSpider):
    name = "traffic_england_gb"
    item_attributes = {
        "operator": "National Highways",
        "operator_wikidata": "Q5760006",
        "extras": Categories.SURVEILLANCE_CAMERA.value,
    }
    start_urls = ["https://www.trafficengland.com/api/cctv/getToBounds?bbox=-7.0,49.0,5.0,56.0"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        page_id = re.match(r".*/(\d+).html", item["website"])[1]
        item["name"] = feature["description"]
        item["image"] = f"https://public.highwaystrafficcameras.co.uk/cctvpublicaccess/images/{page_id}.jpg"
        item["extras"]["contact:webcam"] = item["website"]
        item["extras"]["camera:type"] = "fixed"
        yield item
