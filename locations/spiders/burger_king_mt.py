import scrapy

from locations.dict_parser import DictParser
from locations.spiders.burger_king import BURGER_KING_SHARED_ATTRIBUTES


class BurgerKingMTSpider(scrapy.Spider):
    name = "burger_king_mt"
    item_attributes = BURGER_KING_SHARED_ATTRIBUTES
    start_urls = ["https://burgerking.com.mt/wp-admin/admin-ajax.php?action=get_all_stores"]

    def parse(self, response):
        for location in response.json().values():
            item = DictParser.parse(location)
            item["name"] = location["na"]
            item["phone"] = location["te"]
            item["street"] = location["st"]
            item["city"] = location["ct"]
            item["website"] = location["gu"]
            yield item
