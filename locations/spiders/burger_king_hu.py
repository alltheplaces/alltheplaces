from typing import Any
import chompjs
import scrapy
from scrapy.http import Response
from locations.dict_parser import DictParser
from locations.spiders.burger_king import BURGER_KING_SHARED_ATTRIBUTES


class BurgerKingHUSpider(scrapy.Spider):
    name = "burger_king_hu"
    item_attributes = BURGER_KING_SHARED_ATTRIBUTES
    start_urls = [
        "https://burgerking.hu/ettermeink/",
    ]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        bk_locations = response.xpath('//*[contains(text(),"bkLocations")]/text()').get()
        stores = chompjs.parse_js_object(bk_locations)["restaurants"]
        for store in stores:
            item = DictParser.parse(store)
            item["addr_full"] = store["info"]
            item["street_address"] = store["address"]
            item["website"] = "https://burgerking.hu/"
            yield item
