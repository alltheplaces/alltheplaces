import ast
import json
from typing import Iterable

import scrapy
from scrapy import Request
from scrapy.http import Response, JsonRequest

from locations.dict_parser import DictParser
from locations.items import Feature


class EvereveUSSpider(scrapy.Spider):
    name = "evereve_us"
    item_attributes = {"brand": "Evereve", "brand_wikidata": "Q69891997"}

    def start_requests(self) -> Iterable[Request]:
        yield JsonRequest(url = "https://evereve-prod.labs.wesupply.xyz/searchForStores",method="POST",callback=self.parse)

    def parse(self, response: Response) -> Iterable[Feature]:
        for store in json.loads(response.json())["MetaData"].values():
            store.update(store["Geometry"].pop("location"))
            item = DictParser.parse(store)
            item["ref"] = store["PlaceId"]
            yield item

