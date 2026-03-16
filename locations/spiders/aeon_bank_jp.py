from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import Request, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class AeonBankJPSpider(Spider):
    name = "aeon_bank_jp"

    async def start(self) -> AsyncIterator[Request]:
        yield self.get_page(0)

    def get_page(self, n):
        return Request(
            f"https://map.aeonbank.co.jp/aeonbank/api/proxy2/shop/list?datum=wgs84&limit=500&offset={n}",
            meta={"offset": n},
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        data = response.json()
        stores = data["items"]

        for store in stores:
            item = DictParser.parse(store)
            try:
                match store["categories"][0]["code"]:
                    case "10":
                        item["name"] = "みずほ銀行"
                        item.update({"brand_wikidata": "Q2882956"})
                    case _:
                        item["name"] = "イオン銀行"
                        item.update({"brand_wikidata": "Q11286327"})
            except:
                item["name"] = "イオン銀行"
                item.update({"brand_wikidata": "Q11286327"})

            item["branch"] = store["name"].removesuffix("出張所")
            item["ref"] = store["code"]
            item["lat"] = store["coord"]["lat"]
            item["lon"] = store["coord"]["lon"]
            item["extras"]["branch:ja-Hira"] = store.get("ruby")
            item["addr_full"] = store["address_name"]
            item["postcode"] = store.get("postal_code")
            item["website"] = f"https://map.aeonbank.co.jp/aeonbank/spot/detail?code={store['code']}"

            apply_category(Categories.ATM, item)

            yield item

        if data["count"]["limit"] == len(data["items"]):
            yield self.get_page(data["count"]["limit"] + response.meta["offset"])
