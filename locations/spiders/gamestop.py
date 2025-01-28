from typing import Any, Iterable

from scrapy import Request, Spider
from scrapy.http import JsonRequest, Response

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.spiders.gamestop_us import GAMESTOP_SHARED_ATTRIBUTES


class GamestopSpider(Spider):
    name = "gamestop"
    item_attributes = GAMESTOP_SHARED_ATTRIBUTES

    def start_requests(self) -> Iterable[Request]:
        for country in ["ca", "de", "it"]:
            yield JsonRequest(
                url="https://www.gamestop.{}/api/store/GetNearestStoresByLocation?latitude=0&longitude=0&limit=1000".format(
                    country
                ),
                cb_kwargs={"country": country},
            )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json():
            item = DictParser.parse(store)
            item["branch"] = item.pop("name")
            item["ref"] = "-".join([str(item["ref"]), kwargs["country"]])
            item["country"] = kwargs["country"]
            item["website"] = f"https://www.gamestop.{kwargs['country']}"
            item["opening_hours"] = OpeningHours()
            for day, time in store["hours"].items():
                if time == "Closed":
                    item["opening_hours"].set_closed(day)
                    continue
                open_time, close_time = time.split("–")
                item["opening_hours"].add_range(
                    day=day,
                    open_time=open_time.strip(),
                    close_time=close_time.strip(),
                    time_format="%I:%M %p" if ".ca" in response.url else "%H:%M",
                )
            item["street_address"] = item.pop("addr_full", None)
            yield item
