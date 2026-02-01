from typing import AsyncIterator

from scrapy import Spider
from scrapy.http import Request

from locations.dict_parser import DictParser


class TakarakujiJPSpider(Spider):
    name = "takarakuji_jp"
    country_code = "JP"

    async def start(self) -> AsyncIterator[Request]:
        yield self.get_page(1)

    def get_page(self, n):
        return Request(
            f"https://www.takarakuji-official.jp/map/shoplist/?pageno={n}",
            meta={"page": n},
        )

    def parse(self, response):
        data = response.json()
        shops = data["shops"]

        for shop in shops:
            item = DictParser.parse(shop)
            item["ref"] = shop["id"]
            item["website"] = f"https://www.takarakuji-official.jp/map/spot/?uribaCode={shop['id']}"
            if shop["atm"] == "1":
                item["extras"]["amenity"] = "atm"
            else:
                item["brand_wikidata"] = "Q87824893"
            yield item

        if data["pager"]["pageNumber"] < data["pager"]["totalCount"] // data["pager"]["pageSize"]:
            yield self.get_page(1 + response.meta["page"])
