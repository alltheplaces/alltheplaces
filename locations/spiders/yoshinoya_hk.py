from typing import Any

import scrapy
from scrapy.http import Response

from locations.dict_parser import DictParser


class YoshinoyaHKSpider(scrapy.Spider):
    name = "yoshinoya_hk"
    item_attributes = {"brand": "Yoshinoya", "brand_wikidata": "Q776272"}
    start_urls = [
        "https://www.yoshinoya.com.hk/wp-admin/admin-ajax.php?action=store_search&lat=22.396428&lng=114.109497"
    ]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for restaurant in response.json():
            item = DictParser.parse(restaurant)
            item["branch"] = restaurant["store"]
            yield item
