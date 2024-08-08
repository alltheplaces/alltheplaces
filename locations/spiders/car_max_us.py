from typing import Any
from urllib.parse import urljoin

from scrapy import Spider
from scrapy.http import Response

from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import merge_address_lines
from locations.user_agents import FIREFOX_LATEST


class CarMaxUSSpider(Spider):
    name = "car_max_us"
    item_attributes = {"brand": "CarMax", "brand_wikidata": "Q5037190"}
    start_urls = ["https://www.carmax.com/stores/api/all"]
    user_agent = FIREFOX_LATEST

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json():
            if location["activeStatus"] != "Active":
                continue
            item = DictParser.parse(location)
            item["branch"] = item.pop("name")
            item["street_address"] = merge_address_lines([location["addressLine1"], location["addressLine2"]])
            item["state"] = location["stateAbbreviation"]
            item["website"] = urljoin("https://www.carmax.com/stores/", location["id"])

            yield item
