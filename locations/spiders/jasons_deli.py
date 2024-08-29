import pprint
import re
from typing import Any
from requests_cache import Response
from scrapy.http import JsonRequest

import scrapy

from locations.dict_parser import DictParser
from locations.hours import OpeningHours, DAYS
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class JasonsDeliSpider(scrapy.Spider):
    name = "jasons_deli"
    item_attributes = {"brand": "Jason's Deli", "brand_wikidata": "Q16997641"}
    allowed_domains = ["jasonsdeli.com"]

    def start_requests(self):
        yield JsonRequest(
            url="https://jdapi.jasonsdeli.com/api/v1/stores",
            headers={"x-api-key": "683d4f90-1e20-11ef-9b2d-bf7a8563af57",
                     "x-application-name": "jd-website-2024" },
        )


    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json():
            if location["isActive"]:
                item = DictParser.parse(location)
                yield item


