from typing import Any

import scrapy
from scrapy.http import Response

from locations.dict_parser import DictParser


class CookoutSpider(scrapy.Spider):
    name = "cookout"
    item_attributes = {"brand": "Cook Out", "brand_wikidata": "Q5166992"}
    start_urls = [
        "https://cookout.com/wp-admin/admin-ajax.php?action=store_search&lat=40.71278&lng=-74.00597&max_results=500&search_radius=1000"
    ]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json():
            item = DictParser.parse(store)
            item["street_address"] = item.pop("addr_full")
            item["branch"] = store.get("store")
            yield item
