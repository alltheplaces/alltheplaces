import re
from typing import Any

import scrapy
from scrapy.http import JsonRequest, Response

from locations.dict_parser import DictParser


class GodfathersPizzaSpider(scrapy.Spider):
    name = "godfathers_pizza"
    item_attributes = {"brand": "Godfather's Pizza", "brand_wikidata": "Q5576353"}
    # start_urls = ["https://godfathers.orderexperience.net/_nuxt/dbf11b2.js"]
    start_urls = [
        "https://godfathers.orderexperience.net/locations?_gl=1*wnu5aw*_gcl_au*MjAzNTAxNDc1OC4xNzYxODMwODU1*_ga*MjEwODI5ODM0My4xNzYxODMwODU1*_ga_TG5PXZSCYT*czE3NjE4MzA4NTUkbzEkZzEkdDE3NjE4MzA4NTgkajU3JGwwJGgw"
    ]

    def parse(self, response):
        yield scrapy.Request(
            url="https://godfathers.orderexperience.net" + response.xpath("/html/body/script[4]/@src").get(),
            callback=self.parse_token,
        )

    def parse_token(self, response: Response, **kwargs: Any) -> Any:
        key = re.search(r"apiKey:\s*\"(\w+)\"", response.text).group(1)
        yield JsonRequest(
            url="https://oxb.pxsweb.com/api/v1/apps/restaurants/66abfd6ce1b9d093ee0ab75d?key={}".format(key),
            callback=self.parse_store,
        )

    def parse_store(self, response):
        for store in response.json():
            item = DictParser.parse(store)
            if store["loc"]:
                item["lat"] = store["loc"][0]
                item["lon"] = store["loc"][1]
            if item.get("addr_full"):
                item["street_address"] = item.pop("addr_full")
            yield item
