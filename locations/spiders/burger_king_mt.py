import json
import re

import scrapy
from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.spiders.burger_king import BURGER_KING_SHARED_ATTRIBUTES
from locations.user_agents import BROWSER_DEFAULT


class BurgerKingMTSpider(Spider):
    name = "burger_king_mt"
    item_attributes = BURGER_KING_SHARED_ATTRIBUTES
    # start_urls = ["https://burgerking.com.mt/stores"]
    custom_settings = {"ROBOTSTXT_OBEY": False, "USER_AGENT": BROWSER_DEFAULT, "DOWNLOAD_TIMEOUT": 110}

    async def start(self):
        yield scrapy.Request(url="https://burgerking.com.mt/stores")

    def parse(self, response):
        raw_data = json.loads(re.search(r"locations\":(\[.+\]),\"locations_catering", response.text).group(1))
        for location in raw_data:
            item = DictParser.parse(location)
            item["branch"] = item.pop("name").replace("BURGER KING ", "")
            apply_category(Categories.FAST_FOOD, item)
            yield item
