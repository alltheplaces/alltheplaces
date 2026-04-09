from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class RouteinnJPSpider(Spider):
    name = "routeinn_jp"
    item_attributes = {"brand": "ホテルルートイン", "brand_wikidata": "Q11337912"}

    async def start(self) -> AsyncIterator[JsonRequest]:
        for points in [
            "w",
            "x",
            "z",
        ]:
            yield JsonRequest(url=f"https://route-inn.storelocator.jp/api/point/{points}/")

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json()["items"]:

            item = DictParser.parse(store)

            item["website"] = store["extra_fields"]["詳細ページへのリンク"]
            item["extras"]["website:booking"] = store["extra_fields"]["予約ページURL（PC）"]
            item["postcode"] = store["extra_fields"]["postal_code"]
            item["phone"] = f"+81 {store['extra_fields']['phone']}"
            item["branch"] = store["name"].removeprefix("ホテルルートイン")
            item["extras"]["branch:en"] = store["extra_fields"]["name.en"].removeprefix("HOTEL ROUTE INN ").title()
            apply_category(Categories.HOTEL, item)
            item["name"] = "ホテルルートイン"
            yield item
