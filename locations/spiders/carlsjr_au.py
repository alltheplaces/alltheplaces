import re

import chompjs
import scrapy

from locations.dict_parser import DictParser


class CarlsJrUSSpider(scrapy.Spider):
    name = "carlsjr_au"
    item_attributes = {"brand": "Carl's Jr.", "brand_wikidata": "Q1043486"}
    start_urls = [
        "https://cdncf.storelocatorwidgets.com/json/8OcbNq74HmDWk0HlBmrz4u2nLczZSJf8?callback=slw&_=1714380469680"
    ]

    def parse(self, response, **kwargs):
        for store in chompjs.parse_js_object(
            re.search(r"stores\":\s*(\[.*\]),\s*\"display_order_set", response.text, re.DOTALL).group(1)
        ):
            store.update(store.pop("data"))
            item = DictParser.parse(store)
            item["lat"] = store.get("map_lat")
            item["lon"] = store.get("map_lng")
            item["website"] = "https://carlsjr.com.au/"
            yield item
