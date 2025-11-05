from typing import AsyncIterator

from scrapy import Spider
from scrapy.http import Request

from locations.dict_parser import DictParser


class AcomJPSpider(Spider):
    name = "acom_jp"

    item_attributes = {
        "brand": "アコム",
        "brand_wikidata": "Q4674469",
        "extras": {
            "brand:en": "Acom",
            "shop": "money_lender",
        },
    }

    async def start(self) -> AsyncIterator[Request]:
        yield self.get_page(0)

    def get_page(self, n):
        return Request(
            f"https://store.acom.co.jp/acomnavi/api/proxy2/shop/list?limit=500&offset={n}",
            meta={"offset": n},
        )

    def parse(self, response):
        data = response.json()
        stores = data["items"]

        for store in stores:
            item = DictParser.parse(store)
            item["name"] = "アコム"
            item["branch"] = store["name"]
            item["ref"] = store["code"]
            item["lat"] = store["coord"]["lat"]
            item["lon"] = store["coord"]["lon"]
            item["extras"]["branch:ja-Hira"] = store["ruby"]
            item["addr_full"] = store["address_name"]
            item["website"] = f"https://store.acom.co.jp/acomnavi/spot/detail?code={store['code']}"
            yield item

        if data["count"]["limit"] == len(data["items"]):
            yield self.get_page(data["count"]["limit"] + response.meta["offset"])
