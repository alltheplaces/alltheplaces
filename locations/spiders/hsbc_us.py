import json
from typing import Any

from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.dict_parser import DictParser
from locations.spiders.hsbc import HsbcSpider


class HsbcUSSpider(CrawlSpider):
    name = "hsbc_us"
    item_attributes = HsbcSpider.item_attributes
    start_urls = ["https://www.us.hsbc.com/wealth-center/list/"]
    rules = [Rule(LinkExtractor(allow=r"/wealth-center/list/"), callback="parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        raw_data = json.loads(response.xpath('//*[@type= "application/ld+json"]/text()').get())
        item = DictParser.parse(raw_data)
        item["ref"] = item["website"] = response.url
        yield item
