from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours
from locations.user_agents import BROWSER_DEFAULT


class ShopkoSpider(Spider):
    name = "shopko"
    item_attributes = {"brand": "Shopko Optical", "brand_wikidata": "Q109228833"}

    async def start(self) -> AsyncIterator[Any]:
        yield JsonRequest(
            url="https://api.scheduler.fielmannusa.com/api/auth/login",
            headers={"user-agent": BROWSER_DEFAULT},
            method="POST",
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        yield JsonRequest(
            url="https://api.scheduler.fielmannusa.com/api/FindNearestRetailStores?bn=shopko",
            data={"latitude": 41.8780025, "longitude": -93.097702},
            headers={"authorization": "Bearer " + response.json()["token"]},
            method="POST",
            callback=self.parse_details,
        )

    def parse_details(self, response: Response) -> Any:
        for store in response.json():
            item = DictParser.parse(store)
            item["branch"] = item.pop("name")
            oh = OpeningHours()
            for day, time in store["openingHours"].items():
                day = DAYS_FULL[int(day)]
                open_time, close_time = time.split(" - ")
                oh.add_range(day=day, open_time=open_time, close_time=close_time, time_format="%H:%M %p")
            item["opening_hours"] = oh
            yield item
