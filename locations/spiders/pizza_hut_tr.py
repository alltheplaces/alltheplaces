import re

import scrapy
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.spiders.pizza_hut_us import PizzaHutUSSpider


class PizzaHutTRSpider(scrapy.Spider):
    name = "pizza_hut_tr"
    item_attributes = PizzaHutUSSpider.PIZZA_HUT
    start_urls = ["https://www.pizzahut.com.tr/static/js/main.c39af298.chunk.js"]

    def parse(self, response, **kwargs):
        if match := re.search(r"Username[:\s]+\"(.+?)\"[\s,]+Password[:\s]+\"(.+?)\"", response.text):
            yield JsonRequest(
                url="https://auth.pizzahut.com.tr/api/auth/AuthService",
                data={"Username": match.group(1), "Password": match.group(2)},
                callback=self.parse_token,
            )

    def parse_token(self, response):
        access_token = response.json()["access_token"]
        yield JsonRequest(
            url="https://api.pizzahut.com.tr/api/web/Restaurants/GetRestaurants?getAll=true",
            headers={"Authorization": f"Bearer {access_token}"},
            callback=self.parse_stores,
        )

    def parse_stores(self, response):
        for store in response.json()["result"]:
            item = DictParser.parse(store)
            if item["lat"] and item["lon"]:
                item["lat"] = item["lat"].replace(",", ".")
                item["lon"] = item["lon"].replace(",", ".")
            yield item
