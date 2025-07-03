import json
from typing import Any

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class LatvijasPastsLVSpider(Spider):
    name = "latvijas_pasts_lv"
    item_attributes = {"brand": "Latvijas Pasts", "brand_wikidata": "Q1807088"}

    def start_requests(self):
        yield JsonRequest(
            url="https://mans.pasts.lv/api/public/addresses/service_location?type[]=7&type[]=6&type[]=1&type[]=2&search=&itemsPerPage=1500&page=1"
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in json.loads(response.text):
            item = DictParser.parse(location)
            item["branch"] = location["label"]
            item["addr_full"] = location["readableAddress"]
            if location["type"] in [1, 2]:
                apply_category(Categories.POST_OFFICE, item)
            elif location["type"] in [6, 7]:
                apply_category(Categories.PARCEL_LOCKER, item)
            item["opening_hours"] = OpeningHours()
            for key, value in location["workingHours"].items():
                day = key
                if value == "-":
                    continue
                for time in value.split(";"):
                    open_time, close_time = time.replace(".", ":").split("-")
                item["opening_hours"].add_range(day=day, open_time=open_time.strip(), close_time=close_time.strip())
            yield item
