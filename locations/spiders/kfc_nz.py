import collections

import scrapy
from scrapy.http import JsonRequest

from locations.categories import Extras, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.spiders.kfc_us import KFC_SHARED_ATTRIBUTES


class KfcNZSpider(scrapy.Spider):
    name = "kfc_nz"
    item_attributes = KFC_SHARED_ATTRIBUTES
    allowed_domains = ["kfc.co.nz"]
    start_urls = ["https://api.kfc.co.nz/configurations"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response, **kwargs):
        for key in response.json()["storeKeys"]:
            yield JsonRequest(url=f"https://api.kfc.co.nz/find-a-kfc/{key}", callback=self.parse_store)

    def parse_store(self, response):
        for location in response.json()["Value"]:
            item = DictParser.parse(location)
            item.pop("addr_full")
            item["street_address"] = location["address"]
            item.pop("state")
            item["website"] = "https://kfc.co.nz/find-a-kfc/" + item["website"]

            apply_yes_no(Extras.DRIVE_THROUGH, item, location["drivethru"], False)
            apply_yes_no(Extras.DELIVERY, item, "delivery" in location["dispositions"], False)

            item["opening_hours"] = OpeningHours()
            day_list = collections.deque(DAYS.copy())
            day_list.rotate(1)
            for hours_range in location["operatingHoursStore"]:
                item["opening_hours"].add_range(
                    day_list[int(hours_range["dayOfWeek"])], hours_range["start"], hours_range["end"]
                )

            yield item
