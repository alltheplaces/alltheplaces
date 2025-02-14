import re
from typing import Any

import scrapy
from scrapy.http import JsonRequest, Response

from locations.dict_parser import DictParser


class GodfathersPizzaSpider(scrapy.Spider):
    name = "godfathers_pizza"
    item_attributes = {"brand": "Godfather's Pizza", "brand_wikidata": "Q5576353"}
    start_urls = ["https://godfathers.orderexperience.net/_nuxt/aa3a1a2.js"]
    requires_proxy = True

    def parse(self, response: Response, **kwargs: Any) -> Any:
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
            item["street_address"] = item.pop("addr_full")
            yield item
