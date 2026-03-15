from typing import AsyncIterator

from scrapy import Spider
from scrapy.http import Request

from locations.dict_parser import DictParser


class SaizeriyaSpider(Spider):
    name = "saizeriya"

    item_attributes = {
        "brand_wikidata": "Q886564",
    }
    custom_settings = {"ROBOTSTXT_OBEY": False}
    skip_auto_cc_domain = True

    async def start(self) -> AsyncIterator[Request]:
        yield self.get_page(0)

    def get_page(self, n):
        return Request(
            f"https://shop.saizeriya.co.jp/sz_restaurant/api/proxy2/shop/list?datum=wgs84&limit=500&offset={n}",
            meta={"offset": n},
        )

    def parse(self, response):
        data = response.json()
        stores = data["items"]

        for store in stores:
            item = DictParser.parse(store)
            # item["name"] = None
            item["branch"] = (
                store["name"].removeprefix("サイゼリヤ ").removeprefix("Saizeriya　 ").removeprefix("Saizeriya ")
            )
            item["ref"] = store["code"]
            item["lat"] = store["coord"]["lat"]
            item["lon"] = store["coord"]["lon"]
            item["postcode"] = store.get("postal_code")
            if ruby := store.get("ruby"):
                item["extras"]["branch:ja-Hira"] = ruby.removeprefix("サイゼリヤ")
            item["addr_full"] = store["address_name"]
            item["website"] = f"https://shop.saizeriya.co.jp/sz_restaurant/spot/detail?code={store['code']}"
            yield item

        if data["count"]["limit"] == len(data["items"]):
            yield self.get_page(data["count"]["limit"] + response.meta["offset"])
