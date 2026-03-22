from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import Request, Response

from locations.items import Feature


class DoutorJPSpider(Spider):
    name = "doutor_jp"
    item_attributes = {"brand": "ドトール", "brand_wikidata": "Q11322732"}

    async def start(self) -> AsyncIterator[Request]:
        yield self.get_page(0)

    def get_page(self, n):
        return Request(
            f"https://shop.doutor.co.jp/doutor/api/proxy2/shop/list?datum=wgs84&limit=500&offset={n}",
            meta={"offset": n},
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        data = response.json()
        stores = data["items"]

        for store in stores:
            item = Feature()
            item["branch"] = store["name"].removeprefix("ドトールコーヒーショップ ")
            item["ref"] = store["code"]
            item["phone"] = f"+81 {store['phone']}"
            item["lat"] = store["coord"]["lat"]
            item["lon"] = store["coord"]["lon"]
            item["addr_full"] = store["address_name"]
            item["postcode"] = store["postal_code"]
            item["website"] = f"https://shop.doutor.co.jp/doutor/spot/detail?code={store['code']}"

            yield item

        if data["count"]["offset"] + data["count"]["limit"] < data["count"]["total"]:
            yield self.get_page(data["count"]["limit"] + response.meta["offset"])
