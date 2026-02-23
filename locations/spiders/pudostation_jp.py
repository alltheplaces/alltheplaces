from typing import AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser


class PudostationJPSpider(Spider):
    name = "pudostation_jp"

    async def start(self) -> AsyncIterator[JsonRequest]:
        for points in ["w", "x", "z"]:
            yield JsonRequest(url=f"https://map.pudo.jp/api/points/{points}")

    item_attributes = {
        "brand_wikidata": "Q86738066",
    }

    def parse(self, response):
        for store in response.json()["items"]:

            item = DictParser.parse(store)
            item["ref"] = store["key"]
            item["website"] = f"https://map.pudo.jp/points/{store['key']}"
            item["postcode"] = store["extra_fields"]["Zip code"]
            try:
                if "24" in store["extra_fields"]["土曜使用可能時間"]:
                    item["opening_hours"] = "24/7"
            except:
                pass

            yield item
