import json
from typing import Any, Iterable

from scrapy import Request, Spider
from scrapy.http import JsonRequest, Response

from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.spiders.burger_king import BURGER_KING_SHARED_ATTRIBUTES


class BurgerKingTWSpider(Spider):
    name = "burger_king_tw"
    item_attributes = BURGER_KING_SHARED_ATTRIBUTES

    def start_requests(self) -> Iterable[Request]:
        yield JsonRequest(
            url="https://www.burgerking.com.tw/AJhandler/frontierHandler.ashx",
            data={"what": "getDeliveryInfo", "args": 520000, "list": {"type": 20, "view": 1}, "args2": ""},
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["args"]["branchList"]:
            item = DictParser.parse(location)
            item["branch"] = item.pop("name")
            item["opening_hours"] = OpeningHours()
            for rule in json.loads(location["openHours"]):
                if not rule["isopen"]:
                    continue
                item["opening_hours"].add_range(DAYS[rule["week"] - 1], rule["openTime"], rule["closeTime"])
            item["website"] = "https://www.burgerking.com.tw/map"
            yield item
