from typing import Iterable

from scrapy.http import Response

from locations.items import Feature
from locations.spiders.nevada_dot_us import NevadaDotUSSpider


class ConnecticutDotUSSpider(NevadaDotUSSpider):
    name = "connecticut_dot_us"
    item_attributes = {"operator": "Connecticut DOT", "operator_wikidata": "Q4923420"}
    start_urls = ["https://ctroads.org/map/mapIcons/Cameras"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        for item in super().post_process_item(item, response, feature):
            item["state"] = "CT"
            yield item
