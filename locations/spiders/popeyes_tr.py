from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.dict_parser import DictParser


class PopeyesTRSpider(Spider):
    name = "popeyes_tr"
    item_attributes = {"brand": "Popeyes", "brand_wikidata": "Q1330910"}
    start_urls = ["https://www.popeyes.com.tr/Restaurants/GetRestaurants/GetRestaurants/"]
    no_refs = True

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json():
            location.update(location.pop("data"))
            item = DictParser.parse(location)
            item["street_address"] = item.pop("addr_full")
            yield item
