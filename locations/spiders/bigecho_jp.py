from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.dict_parser import DictParser


class BigechoJPSpider(Spider):
    name = "bigecho_jp"

    start_urls = ["https://shop.big-echo.jp/api/point"]
    allowed_domains = ["shop.big-echo.jp"]
    item_attributes = {
        "brand_wikidata": "Q15831707",
    }

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json()["items"]:

            item = DictParser.parse(store)

            item["extras"]["amenity"] = "karaoke_box"
            item["website"] = f"https://reserve.big-echo.jp/r/{store['key']}"
            item["ref"] = store["key"]

            yield item
