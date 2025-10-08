from typing import Any

import scrapy
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class BusyBeaverUSSpider(scrapy.Spider):
    name = "busy_beaver_us"
    item_attributes = {
        "brand": "Busy Beaver",
        "brand_wikidata": "Q108394482",
    }
    start_urls = ["https://cdn.builder.io/api/v3/content/store-locator?apiKey=5b1557836a7c4ddcadf9328da7855dc8"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json()["results"][0]["data"]["stores"]:
            item = DictParser.parse(store)
            item["ref"] = store["posId"]
            apply_category(Categories.SHOP_DOITYOURSELF, item)
            yield item
