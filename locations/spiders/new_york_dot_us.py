from typing import Iterable

from scrapy.http import Response

from locations.items import Feature
from locations.pipelines.state_clean_up import StateCodeCleanUpPipeline
from locations.spiders.nevada_dot_us import NevadaDotUSSpider


class NewYorkDotUSSpider(NevadaDotUSSpider):
    name = "new_york_dot_us"
    item_attributes = {"operator": "New York State DOT", "operator_wikidata": "Q527769"}
    start_urls = ["https://511ny.org/map/mapIcons/Cameras"]

    # TODO: better ways?
    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        for item in super().post_process_item(item, response, feature):
            item["country"] = "US"
            StateCodeCleanUpPipeline.clean_state_process_item(item, self)
            if not item["state"] is "CT":
                item["state"] = "NY"
                yield item
