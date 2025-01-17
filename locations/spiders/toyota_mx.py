from typing import Iterable

import scrapy
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.items import Feature
from locations.spiders.toyota_au import TOYOTA_SHARED_ATTRIBUTES


class ToyotaMXSpider(scrapy.Spider):
    name = "toyota_mx"
    item_attributes = TOYOTA_SHARED_ATTRIBUTES
    start_urls = ["https://www.toyota.mx/graphql/execute.json/tmex/distributorByStates"]

    def parse(self, response: Response) -> Iterable[Feature]:
        for data in response.json()["data"]["stateDistributorsList"]["items"]:
            state = data["state"]
            for store in data["distributors"]:
                item = DictParser.parse(store)
                item["ref"] = store["dealerCode"]
                item["addr_full"] = store["address"]["plaintext"]
                item["state"] = state
                apply_category(Categories.SHOP_CAR, item)
                yield item
