import re

import scrapy
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.spiders.kfc_us import KFC_SHARED_ATTRIBUTES


class KfcIDSpider(scrapy.Spider):
    name = "kfc_id"
    item_attributes = KFC_SHARED_ATTRIBUTES
    no_refs = True

    def start_requests(self):
        url = "https://kfcku.com/api/stores?page=1"
        yield JsonRequest(url=url, headers={"X-Requested-With": "XMLHttpRequest"})

    def parse(self, response, **kwargs):
        for store in response.json().get("data"):
            item = DictParser.parse(store)
            item["image"] = store.get("picture")
            item["city"] = store.get("district").get("name")
            item["state"] = store.get("district").get("province").get("name")
            item["opening_hours"] = OpeningHours()
            if store.get("offices") != []:
                item["phone"] = store.get("offices").get("phone")
                if data := store.get("offices").get("working"):
                    open_time, close_time = re.search(r"(\d+:\d+)\s*-\s*(\d+:\d+)", data[0]).groups()
                    for day in DAYS:
                        item["opening_hours"].add_range(day, open_time, close_time)
            else:
                continue

            yield item

        if next_url := response.json().get("next_page_url"):
            yield JsonRequest(url=next_url, headers={"X-Requested-With": "XMLHttpRequest"})
