from typing import AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class CafeAmazonSpider(Spider):
    name = "cafe_amazon"
    item_attributes = {"brand": "คาเฟ่ อเมซอน", "brand_wikidata": "Q43247503"}

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(
            url="https://www.cafe-amazon.com/api/store-list",
            method="POST",
            data={"limit": 10000, "lang": "en"},
            callback=self.parse,
        )

    def parse(self, response, **kwargs):
        for store in response.json()["stores"]:
            item = DictParser.parse(store)
            item["branch"] = item.pop("name")
            apply_category(Categories.CAFE, item)
            yield item
