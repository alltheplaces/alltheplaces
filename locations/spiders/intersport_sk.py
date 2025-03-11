from typing import Any

import scrapy
from scrapy.http import Response

from locations.dict_parser import DictParser
from urllib.parse import urljoin


class IntersportSKSpider(scrapy.Spider):
    name = "intersport_sk"
    item_attributes = {"brand": "Intersport", "brand_wikidata": "Q666888"}
    start_urls = ["https://api-app1.intersport.sk/shops/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json()["data"]["stores"]:
            item = DictParser.parse(store)
            item["website"] = urljoin("https://www.intersport.sk/shop/", item["website"])
            yield item
