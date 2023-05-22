import re

import json5
from scrapy import Spider

from locations.dict_parser import DictParser


class BlueIllusionSpider(Spider):
    name = "blue_illusion"
    item_attributes = {"brand": "Blue Illusion", "brand_wikidata": "Q118464703"}
    start_urls = ["https://www.blueillusion.com/stores"]

    def parse(self, response, **kwargs):
        script = response.xpath('//script[contains(text(), "stores")]/text()').get()
        for location in json5.loads(re.search(r"stores:\s*(\[.+?\])", script, re.DOTALL).group(1)):
            item = DictParser.parse(location)
            item["website"] = response.urljoin(location["url"])

            yield item
