import scrapy

from locations.dict_parser import DictParser
from locations.spiders.burger_king import BurgerKingSpider


class BurgerKingTRSpider(scrapy.Spider):
    name = "burger_king_tr"
    item_attributes = BurgerKingSpider.item_attributes
    start_urls = ["https://www.burgerking.com.tr/Restaurants/GetRestaurants/"]

    def parse(self, response):
        for poi in response.json():
            poi.update(poi.pop("data"))
            item = DictParser.parse(poi)
            item["ref"] = poi.get("title")
            item["street_address"] = item.pop("addr_full", None)
            yield item
