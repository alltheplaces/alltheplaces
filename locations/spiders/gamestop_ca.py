from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.spiders.gamestop_us import GAMESTOP_SHARED_ATTRIBUTES


class GamestopCASpider(Spider):
    name = "gamestop_ca"
    item_attributes = GAMESTOP_SHARED_ATTRIBUTES
    start_urls = ["https://www.gamestop.ca/api/store/GetNearestStoresByLocation?latitude=0&longitude=0&limit=1000"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json():
            item = DictParser.parse(store)
            item["opening_hours"] = OpeningHours()
            for day, time in store["hours"].items():
                if time == "Closed":
                    continue
                open_time, close_time = time.split("–")
                item["opening_hours"].add_range(
                    day=day, open_time=open_time.strip(), close_time=close_time.strip(), time_format="%I:%M %p"
                )
            yield item
