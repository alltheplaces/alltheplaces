import json
from typing import Any, AsyncIterator

from scrapy import Request, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours
from locations.spiders.starbucks_us import STARBUCKS_SHARED_ATTRIBUTES


class StarbucksTHSpider(Spider):
    name = "starbucks_th"
    item_attributes = STARBUCKS_SHARED_ATTRIBUTES
    requires_proxy = True

    def make_request(self, page: int, limit: int = 100) -> Request:
        return Request(
            url=f"https://www.starbucks.co.th/en/find-a-store?page={page}&limit={limit}",
            cb_kwargs={"page": page, "limit": limit},
        )

    async def start(self) -> AsyncIterator[Request]:
        yield self.make_request(1)

    def parse(self, response: Response, page: int, limit: int) -> Any:
        if stores_info := response.xpath('//script[contains(text(), "Latitude")]'):
            stores = json.loads(stores_info.xpath("./text()").re_first(r"\\\"items\\\":(\[.*\]),").replace("\\", ""))
            for store in stores:
                item = DictParser.parse(store)
                item["city"] = store["Sub_District"]  # No detailed address field is present
                item["branch"] = item["extras"]["branch:th"] = store["CommonStoreNameTH"]
                item["extras"]["branch:en"] = item.pop("name")
                item["phone"] = store.get("Mobile")
                item["opening_hours"] = self.parse_opening_hours(store)
                apply_category(Categories.COFFEE_SHOP, item)
                yield item

            if len(stores) == limit:
                yield self.make_request(page + 1, limit)

    def parse_opening_hours(self, store: dict) -> OpeningHours:
        opening_hours = OpeningHours()
        for day in DAYS_FULL:
            open_time, close_time = [
                (store.get(f"{day.lower()}{timing}") or "").split("T")[-1].split(".")[0]
                for timing in ["OpeningTime", "ClosingTime"]
            ]
            opening_hours.add_range(day, open_time, close_time.replace("00:00:00", "23:59:00"), "%H:%M:%S")
        return opening_hours
