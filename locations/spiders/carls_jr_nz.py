from typing import Any
from urllib.parse import urljoin

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours
from locations.spiders.carls_jr_us import CarlsJrUSSpider


class CarlsJrNZSpider(Spider):
    name = "carls_jr_nz"
    item_attributes = CarlsJrUSSpider.item_attributes
    start_urls = ["https://api.carlsjr.co.nz/configurations"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for key in response.json()["storeKeys"]:
            yield JsonRequest(url="https://api.carlsjr.co.nz/stores/{}".format(key), callback=self.parse_details)

    def parse_details(self, response):
        for store in response.json()["Value"]:
            item = DictParser.parse(store)
            item["website"] = urljoin("https://carlsjr.co.nz/find-a-carls/", store["url"])
            item["branch"] = item.pop("name").removeprefix(
                "Carl's Jr ",
            )
            item["opening_hours"] = OpeningHours()
            for day_time in store["operatingHoursStore"]:
                open_time = day_time["start"]
                close_time = day_time["end"]
                day = DAYS_FULL[day_time["dayofweek"]]
                item["opening_hours"].add_range(day=day, open_time=open_time, close_time=close_time)

            yield item
