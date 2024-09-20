import json
import re
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.items import Feature


class GroenrijkNLSpider(Spider):
    name = "groenrijk_nl"
    item_attributes = {"brand": "GroenRijk", "brand_wikidata": "Q2738788"}
    start_urls = ["https://www.groenrijk.nl/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in json.loads(re.search(r"allLocations = (.+);", response.text).group(1)):
            item = Feature()
            item["branch"] = location["name"].removeprefix("GroenRijk ")
            item["addr_full"] = location["address"].replace("<br/>", ", ")
            item["lat"] = location["latitude"]
            item["lon"] = location["longitude"]
            item["ref"] = item["website"] = response.urljoin(location["path"])

            yield item
