from typing import Any

import scrapy
from scrapy.http import Response

from locations.dict_parser import DictParser


class ZabkaPLSpider(scrapy.Spider):
    name = "zabka_pl"
    item_attributes = {"brand": "Żabka", "brand_wikidata": "Q2589061"}
    start_urls = ["https://www.zabka.pl/app/uploads/locator-store-data.json"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json():
            item = DictParser.parse(store)
            yield item
