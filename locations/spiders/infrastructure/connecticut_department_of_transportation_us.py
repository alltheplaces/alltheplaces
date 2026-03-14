import re
from typing import Iterable

from scrapy.http import Response

from locations.items import Feature
from locations.storefinders.traveliq_web_cameras import TravelIQWebCamerasSpider


class ConnecticutDepartmentOfTransportationUSSpider(TravelIQWebCamerasSpider):
    name = "connecticut_department_of_transportation_us"
    item_attributes = {"operator": "Connecticut Department of Transportation", "operator_wikidata": "Q4923420"}
    allowed_domains = ["www.ctroads.org"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if m := re.match(r"CAM (\d+) ", item["name"]):
            item["extras"]["alt_ref"] = m.group(1)
            item["name"] = re.sub(r"^CAM \d+ ", "", item["name"])
        yield item
