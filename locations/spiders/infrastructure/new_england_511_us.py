from typing import Iterable

from scrapy.http import Response

from locations.items import Feature
from locations.storefinders.traveliq_web_cameras import TravelIQWebCamerasSpider


class NewEngland511USSpider(TravelIQWebCamerasSpider):
    name = "new_england_511_us"
    allowed_domains = ["www.newengland511.org"]
    operators = {
        "ME": ("Maine Department of Transportation", "Q4926312"),
        "NH": ("New Hampshire Department of Transportation", "Q5559073"),
        "VT": ("Vermont Agency of Transportation", "Q7921675"),
    }

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if feature["areaId"] in self.operators.keys():
            item["operator"] = self.operators[feature["areaId"]][0]
            item["operator_wikidata"] = self.operators[feature["areaId"]][1]
        else:
            self.logger.warning("Unknown area identifier cannot be mapped to an operator: {}".format(feature["areaId"]))
        yield item
