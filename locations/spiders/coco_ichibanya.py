from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.dict_parser import DictParser
from locations.categories import Categories
from locations.hours import DAYS, OpeningHours


class CocoIchibanyaSpider(Spider):
    name = "coco_ichibanya"
    skip_auto_cc_domain = True
    item_attributes = {"brand": "CoCo Ichibanya", "brand_wikidata": "Q5986105", "extras": Categories.RESTAURANT.value,}

    async def start(self) -> AsyncIterator[JsonRequest]:
        for points in ["g", "t", "q", "w", "x", "8", "9"]:
            yield JsonRequest(url=f"https://worldwide.ichibanya.co.jp/api/point/{points}/")

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json()["items"]:

            item = DictParser.parse(store)
            item["branch"] = store["name"].replace("店", "")
            item["ref"] = store["key"]
            try:
                item["opening_hours"] = OpeningHours()
                item["opening_hours"].add_days_range(
                    DAYS,
                    store["extra_fields"]["営業時間(From)"].replace("：", ":"),
                    store["extra_fields"]["営業時間(To)"].replace("：", ":"),
                )
            except:
                pass
            item["name"] = None
            yield item
