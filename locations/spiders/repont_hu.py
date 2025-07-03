from typing import Iterable

import scrapy
from scrapy.http import JsonRequest, Request

from locations.dict_parser import DictParser


class RepontHUSpider(scrapy.Spider):
    name = "repont_hu"
    item_attributes = {
        "brand": "REpont",
        "brand_wikidata": "Q130348902",
        "operator": "MOHU MOL Hulladékgazdálkodási Zrt.",
        "operator_wikidata": "Q130207606",
    }
    start_urls = ["https://map.mohu.hu/api/Map/GetAllPois"]

    def parse(self, response) -> Iterable[Request]:
        for poi in response.json():
            yield JsonRequest(
                f"https://map.mohu.hu/api/Map/GetWastePointDetails?id={poi['id']}", callback=self.parse_details
            )

    def parse_details(self, response):
        item = DictParser.parse(response.json())
        item["street_address"] = item.pop("addr_full")
        yield item
