import json
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class MinimartBGSpider(Spider):
    name = "minimart_bg"
    item_attributes = {"brand": "Minimart", "brand_wikidata": "Q119168386"}
    start_urls = ["https://mini-mart.bg/wp-admin/admin-ajax.php?action=asl_load_stores"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json():
            item = DictParser.parse(store)
            item["website"] = "https://mini-mart.bg/"
            item["opening_hours"] = OpeningHours()
            for key, value in json.loads(store["open_hours"]).items():
                day = key
                for time in value:
                    open_time, close_time = time.split(" - ")
                    if "AM" in open_time and "PM" in close_time:
                        item["opening_hours"].add_range(
                            day=day, open_time=open_time, close_time=close_time, time_format="%I:%M %p"
                        )
                    else:
                        item["opening_hours"].add_range(
                            day=day,
                            open_time=open_time,
                            close_time=close_time,
                        )

            yield item
