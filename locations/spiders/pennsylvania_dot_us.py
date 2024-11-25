from typing import Iterable

from scrapy.http import Response

from locations.items import Feature
from locations.spiders.nevada_dot_us import NevadaDotUSSpider


class PennsylvaniaDotUSSpider(NevadaDotUSSpider):
    name = "pennsylvania_dot_us"
    item_attributes = {"operator": "Pennsylvania DOT", "operator_wikidata": "Q5569650"}
    start_urls = ["https://www.511pa.com/map/mapIcons/Cameras"]

    # TODO: better solved with a "dot_pa_us.py" naming convention and handled in pipeline?
    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        # make sure state is PA, some get mis-coded.
        for item in super().post_process_item(item, response, feature):
            item["state"] = "PA"
            yield item
