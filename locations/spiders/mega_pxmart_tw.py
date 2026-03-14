from typing import AsyncIterator, Iterable

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.items import Feature


class MegaPxmartTWSpider(Spider):
    name = "mega_pxmart_tw"
    item_attributes = {"brand": "大全聯", "brand_wikidata": "Q135550746"}

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(url="https://www.pxmart.com.tw/mega/api/stores", method="POST")

    def parse(self, response: Response) -> Iterable[Feature]:
        for location in response.json()["data"]:
            location.update(location.pop("attributes", {}))
            item = DictParser.parse(location)
            item["branch"] = item.pop("name")
            item["addr_full"] = item.pop("street")
            apply_category(Categories.SHOP_SUPERMARKET, item)
            yield item
