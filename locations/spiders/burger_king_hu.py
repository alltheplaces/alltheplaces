from typing import Any

from chompjs import parse_js_object
from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.spiders.burger_king import BURGER_KING_SHARED_ATTRIBUTES


class BurgerKingHUSpider(Spider):
    name = "burger_king_hu"
    item_attributes = BURGER_KING_SHARED_ATTRIBUTES
    start_urls = [
        "https://burgerking.hu/ettermeink/",
    ]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        bk_locations = response.xpath('//*[contains(text(),"bkLocations")]/text()').get()
        stores = parse_js_object(bk_locations)["restaurants"]
        for store in stores:
            item = DictParser.parse(store)
            item["addr_full"] = store["info"]
            item["street_address"] = store["address"]
            item["website"] = "https://burgerking.hu/"
            apply_category(Categories.FAST_FOOD, item)
            yield item
