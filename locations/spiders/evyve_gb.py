import json
import re
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import merge_address_lines


class EvyveGBSpider(Spider):
    name = "evyve_gb"
    item_attributes = {"operator": "evyve", "operator_wikidata": "Q116698197"}
    start_urls = ["https://evyve.co.uk/locations/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in json.loads(
            re.search(
                r"propertyLocations = JSON\.parse\('(\[.+])'",
                response.xpath('//script[contains(text(), "propertyLocations")]/text()').get(),
            ).group(1)
        ):
            if location["visibility"] != "public":
                continue
            item = DictParser.parse(location)
            item["street_address"] = merge_address_lines(
                [
                    location["location"]["address"]["address1"],
                    location["location"]["address"]["address2"],
                    location["location"]["address"]["address3"],
                ]
            )
            item["city"] = location["location"]["address"]["city"]
            item["postcode"] = location["location"]["address"]["zip"]
            item["lat"] = location["location"]["coordinates"]["latitude"]
            item["lon"] = location["location"]["coordinates"]["longitude"]
            item["extras"]["start_date"] = location["metadata"]["openingDate"]

            apply_category(Categories.CHARGING_STATION, item)

            yield item
