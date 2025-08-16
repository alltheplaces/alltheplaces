from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.dict_parser import DictParser


class AifulJPSpider(Spider):
    name = "aiful_jp"

    start_urls = ["https://shop.aiful.co.jp/api/poi"]
    allowed_domains = ["shop.aiful.co.jp"]
    country_code = "JP"

    item_attributes = {
        "brand_wikidata": "Q4696808",
        "brand": "アイフル",
        "extras": {
            "brand:en": "Aiful",
            "shop": "money_lender",
            # TODO: add to NSI
        },
    }

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json():

            item = DictParser.parse(store)
            item["ref"] = store["key"]
            item["website"] = f"https://shop.aiful.co.jp/map/{store['key']}"

            yield item
