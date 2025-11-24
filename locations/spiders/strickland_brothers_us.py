import json
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.dict_parser import DictParser


class StricklandBrothersUSSpider(Spider):
    name = "strickland_brothers_us"
    item_attributes = {"brand": "Strickland Brothers", "brand_wikidata": "Q122811625"}
    start_urls = ["https://sboilchange.com/locations/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in json.loads(
            response.xpath('//script[contains(text(), "dataPoints")]/text()').re_first(r"dataPoints = (\[.+\]);")
        ):
            item = DictParser.parse(location)
            item["street_address"] = item.pop("street")
            item["name"] = None
            yield item
