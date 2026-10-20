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
        match = re.search(r"locations\":(\[.+\]),\"locations_catering", response.text)
        if not match:
            self.logger.error("Could not extract locations from response")
            return
        raw_data = json.loads(match.group(1))
        for location in raw_data:
            item = DictParser.parse(location)
            if "name" in item:
                item["branch"] = item.pop("name").replace("BURGER KING ", "")
            apply_category(Categories.FAST_FOOD, item)
            yield item
