from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import Request, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class SevenBankJPSpider(Spider):
    name = "seven_bank_jp"
    item_attributes = {"brand": "セブン銀行", "brand_wikidata": "Q7457182"}

    async def start(self) -> AsyncIterator[Request]:
        yield self.get_page(0)

    def get_page(self, n):
        return Request(
            f"https://location.sevenbank.co.jp/sevenbank/api/proxy2/shop/list?datum=wgs84&limit=500&offset={n}",
            meta={"offset": n},
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        data = response.json()
        stores = data["items"]

        for store in stores:
            item = DictParser.parse(store)
            item["name"] = "セブン銀行"
            item["branch"] = store["name"].removesuffix("　共同出張所")
            item["ref"] = store["code"]
            item["lat"] = store["coord"]["lat"]
            item["lon"] = store["coord"]["lon"]
            item["extras"]["branch:ja-Hira"] = store["ruby"]
            item["addr_full"] = store["address_name"]
            item["postcode"] = store["postal_code"]
            item["website"] = f"https://location.sevenbank.co.jp/sevenbank/spot/detail?code={store['code']}"

            apply_category(Categories.ATM, item)

            yield item

        if data["count"]["limit"] == len(data["items"]):
            yield self.get_page(data["count"]["limit"] + response.meta["offset"])
