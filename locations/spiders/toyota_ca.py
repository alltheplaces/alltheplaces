import datetime
from copy import deepcopy
from typing import AsyncIterator, Iterable

from scrapy import Spider
from scrapy.http import Request, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.items import Feature
from locations.spiders.toyota_au import TOYOTA_SHARED_ATTRIBUTES
from locations.spiders.toyota_eu import LEXUS_SHARED_ATTRIBUTES

current_day = (datetime.datetime.now()).strftime("%A")


class ToyotaCASpider(Spider):
    name = "toyota_ca"
    BRAND_MAPPING = {
        "toyota": TOYOTA_SHARED_ATTRIBUTES,
        "lexus": LEXUS_SHARED_ATTRIBUTES,
    }

    async def start(self) -> AsyncIterator[Request]:
        for brand in self.BRAND_MAPPING:
            yield Request(
                f"https://www.toyota.ca/bin/find_a_dealer/dealersList?brand={brand}&language=en&userInput=vancover&latitude=49.2827291&longitude=-123.1207375&scenario=proximity&dayOfWeek={current_day}",
                meta={"brand": brand},
            )

    def parse(self, response: Response) -> Iterable[Feature]:
        for location in response.json()["dealers"]:
            item = DictParser.parse(location)
            item["ref"] = location["dealerCode"]
            item["street_address"] = item.pop("addr_full")

            if brand_attributes := self.BRAND_MAPPING.get(response.meta["brand"]):
                item["brand"] = brand_attributes["brand"]
                item["brand_wikidata"] = brand_attributes["brand_wikidata"]

            shop_item = deepcopy(item)
            apply_category(Categories.SHOP_CAR, shop_item)
            yield shop_item

            # I couldn't find a way to distinguish between service and shop locations,
            # but after some manual checks, it seems that all locations have a service
            service_item = deepcopy(item)
            service_item["ref"] = f"{item['ref']}-SERVICE"
            apply_category(Categories.SHOP_CAR_REPAIR, service_item)
            yield service_item
