import json
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class WholeFoodsGBSpider(Spider):
    name = "whole_foods_gb"
    item_attributes = {"brand": "Whole Foods Market", "brand_wikidata": "Q1809448"}
    start_urls = ["https://www.wholefoodsmarket.co.uk/find-a-store"]
    no_refs = True

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.xpath("//@data-block-json").getall():
            location = json.loads(location)["location"]
            item = Feature()
            item["lat"] = location["markerLat"]
            item["lon"] = location["markerLng"]
            item["name"] = location["addressTitle"]
            item["addr_full"] = merge_address_lines([location["addressLine1"], location["addressLine2"]])
            item["country"] = location["addressCountry"]
            yield item
