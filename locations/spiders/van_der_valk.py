import json
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class VanDerValkSpider(Spider):
    name = "van_der_valk"
    item_attributes = {"brand": "Van der Valk", "brand_wikidata": "Q2802214"}
    start_urls = ["https://www.valk.com/hotels"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        state = json.loads(response.xpath('//script[@id="valkContentApp-state"]/text()').get())
        for hotel in state["filterable-list-valkcom/hotels?language=nl"]["hotels"]:
            name = hotel.pop("name")
            item = DictParser.parse(hotel)
            item["ref"] = hotel["guid"]
            item["branch"] = name
            item["website"] = hotel["toUrl"]
            apply_category(Categories.HOTEL, item)
            yield item
