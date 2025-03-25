from typing import Any

from chompjs import chompjs
from scrapy.http import Response
from scrapy.spiders import Spider

from locations.dict_parser import DictParser
from locations.spiders.taco_bell_us import TACO_BELL_SHARED_ATTRIBUTES


class TacoBellFISpider(Spider):
    name = "taco_bell_fi"
    item_attributes = TACO_BELL_SHARED_ATTRIBUTES
    start_urls = ["https://tacobell.fi/ravintolat/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in chompjs.parse_js_object(response.xpath('//*[@class="restaurants-listing"]/@data-raw').get()):
            item = DictParser.parse(store)
            item["branch"] = item.pop("name").removeprefix("Taco Bell ")
            item["street_address"] = item.pop("addr_full")
            yield item
