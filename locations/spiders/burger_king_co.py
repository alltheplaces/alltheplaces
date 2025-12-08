from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.dict_parser import DictParser
from locations.spiders.burger_king import BURGER_KING_SHARED_ATTRIBUTES

"""
https://api-mena.menu.app/api/directory/search is not properly working for Burger King CO.
Alternate API found on the website's order page https://pideenlinea.bk.com.co/pide-a-domicilio , is being utilized.
"""


class BurgerKingCOSpider(Spider):
    name = "burger_king_co"
    item_attributes = BURGER_KING_SHARED_ATTRIBUTES
    start_urls = ["https://api01.inoutdelivery.com.co/v1/point-sales?business=burgerking.inoutdelivery.com"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json():
            item = DictParser.parse(location)
            item["street_address"] = item.pop("addr_full")
            item["branch"] = item.pop("name")
            # hours =location.get("schedules")
            # opening_hours don't match with Google Maps data, hence skipped.
            yield item
