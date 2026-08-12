import json
import re

from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.spiders.burger_king import BURGER_KING_SHARED_ATTRIBUTES


class BurgerKingMTSpider(Spider):
    name = "burger_king_mt"
    item_attributes = BURGER_KING_SHARED_ATTRIBUTES
    start_urls = ["https://burgerking.com.mt/stores"]

    def parse(self, response):
        raw_data = json.loads(re.search(r"locations\":(\[.+\]),\"locations_catering", response.text).group(1))
        for location in raw_data:
            item = DictParser.parse(location)
            item["branch"] = item.pop("name").replace("BURGER KING ", "")
            apply_category(Categories.FAST_FOOD, item)
            yield item
