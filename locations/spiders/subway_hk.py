import json

import scrapy

from locations.dict_parser import DictParser
from locations.spiders.subway import SubwaySpider


class SubwayHKSpider(scrapy.Spider):
    name = "subway_hk"
    item_attributes = SubwaySpider.item_attributes
    start_urls = ["https://www.subway.com.hk/find-restaurant/"]

    def parse(self, response, **kwargs):
        data = json.loads(
            response.xpath('//script[contains(text(), "var stores")]/text()').re_first(r"var stores = (\{.*\});")
        )
        for store in data.values():
            item = DictParser.parse(store)
            item["website"] = "https://www.subway.com.hk/"
            yield item
