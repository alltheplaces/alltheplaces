import json
from typing import AsyncIterator, Iterable

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.dict_parser import DictParser
from locations.items import Feature


class EvereveUSSpider(Spider):
    name = "evereve_us"
    item_attributes = {"brand": "Evereve", "brand_wikidata": "Q69891997"}

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(
            url="https://evereve-prod.labs.wesupply.xyz/searchForStores", method="POST", callback=self.parse
        )

    def parse(self, response: Response) -> Iterable[Feature]:
        for store in json.loads(response.json())["MetaData"].values():
            store.update(store["Geometry"].pop("location"))
            item = DictParser.parse(store)
            item["ref"] = store["PlaceId"]
            yield item
