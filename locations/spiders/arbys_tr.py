from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.dict_parser import DictParser
from locations.spiders.arbys_us import ArbysUSSpider


class ArbysTRSpider(Spider):
    name = "arbys_tr"
    item_attributes = ArbysUSSpider.item_attributes
    start_urls = ["https://www.arbys.com.tr/Restaurants/GetRestaurants/"]
    no_refs = True

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json():
            location.update(location.pop("data"))
            item = DictParser.parse(location)
            item["street_address"] = item.pop("addr_full")
            item["website"] = "https://www.arbys.com.tr/restoranlar"
            yield item
