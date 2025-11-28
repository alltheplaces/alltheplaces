import json
from typing import AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser


class DunkinSASpider(Spider):
    name = "dunkin_sa"
    item_attributes = {"brand_wikidata": "Q847743"}

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(
            url="https://www.dunkinksa.com/asmx/WebMethods.asmx/getMapStoresList",
            data={"searchVal": "", "latitude": "24.7136", "longitude": "46.6753", "allowString": ""},
        )

    def parse(self, response, **kwargs):
        for store in json.loads(response.json()["d"]):
            item = DictParser.parse(store)
            item["branch"] = item.pop("name")
            item["addr_full"] = store.get("fullAddress")
            yield item
