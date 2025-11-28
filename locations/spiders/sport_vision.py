import json
import re
from typing import Any

from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.dict_parser import DictParser


class SportVisionSpider(CrawlSpider):
    name = "sport_vision"
    item_attributes = {"brand": "Sport Vision", "brand_wikidata": "Q116729857"}
    start_urls = ["https://www.sportvision.group/"]
    rules = [
        Rule(
            LinkExtractor(restrict_xpaths='//*[@id = "countries"]', allow=r"https://sportvision.group/en/country/*"),
            callback="parse",
        ),
    ]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        raw_data = re.search(
            r"var\s+poslovnice\s*=\s*(\[\{.*?\}\])", response.xpath('//*[contains(text(),"poslovnice")]/text()').get()
        ).group(1)
        for store in json.loads(raw_data):
            item = DictParser.parse(store)
            item["website"] = response.url
            item["country"] = response.url.split("/")[-1]
            yield item
