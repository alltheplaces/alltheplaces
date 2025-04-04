import datetime
from typing import Iterable

import scrapy
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.items import Feature
from locations.spiders.toyota_au import TOYOTA_SHARED_ATTRIBUTES

current_day = (datetime.datetime.now()).strftime("%A")


class ToyotaCASpider(scrapy.Spider):
    name = "toyota_ca"
    item_attributes = TOYOTA_SHARED_ATTRIBUTES
    start_urls = [
        "https://www.toyota.ca/bin/find_a_dealer/dealersList?brand=toyota&language=en&userInput=vancover&latitude=49.2827291&longitude=-123.1207375&scenario=proximity&dayOfWeek={}".format(
            current_day
        )
    ]

    def parse(self, response: Response) -> Iterable[Feature]:
        for location in response.json()["dealers"]:
            item = DictParser.parse(location)
            item["ref"] = location["dealerCode"]
            item["street_address"] = item.pop("addr_full")
            apply_category(Categories.SHOP_CAR, item)
            yield item
