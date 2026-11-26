from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class OspreyGBSpider(Spider):
    name = "osprey_gb"
    item_attributes = {"operator": "Osprey", "operator_wikidata": "Q117706577"}
    start_urls = [
        "https://apigw.ospreycharging.co.uk/portal/location/map?filter=box(coordinates,-90.0,-180.0,90.0,180.0)%E2%88%A7evses.status%E2%88%89%7BREMOVED%7D"
    ]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json():
            item = DictParser.parse(location)
            item["street_address"] = item.pop("addr_fukk")
            apply_category(Categories.CHARGING_STATION, item)
            yield item
