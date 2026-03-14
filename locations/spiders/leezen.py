from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class LeezenSpider(Spider):
    name = "leezen"
    item_attributes = {
        "brand": "里仁",
        "brand_wikidata": "Q126368246",
    }
    skip_auto_cc_domain = True

    async def start(self) -> AsyncIterator[JsonRequest]:
        for location_type in [0, 1]:  # 0: TW, 1: Overseas
            yield JsonRequest(
                url="https://ec-app.leezen.com.tw/api/v1/store/list",
                data={"offset": 0, "limit": 1000, "type": location_type, "region": 0},
            )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json()["data"]["rows"]:
            yield JsonRequest(
                url=f'https://ec-app.leezen.com.tw/api/v1/store/detail/{store["no"]}',
                callback=self.parse_store,
                cb_kwargs=dict(store_no=store["no"]),
            )

    def parse_store(self, response: Response, store_no: str) -> Any:
        store = response.json()["data"]["detail"]
        if store.get("type", "") == 1 and not any(
            name in store["name"] for name in ["Leezen", "里仁"]
        ):  # overseas locations, mostly stockists
            return
        item = DictParser.parse(store)
        item["ref"] = store_no
        item["website"] = f"https://www.leezen.com.tw/store/detail/{store_no}"
        item["branch"] = item.pop("name").removeprefix("Leezen Store").strip(", ")
        apply_category(Categories.SHOP_SUPERMARKET, item)
        yield item
