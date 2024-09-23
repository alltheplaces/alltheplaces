import re
from urllib.parse import urljoin

import scrapy

from locations.dict_parser import DictParser
from locations.hours import DAYS_GR, OpeningHours, sanitise_day


class VodafoneGRSpider(scrapy.Spider):
    name = "vodafone_gr"
    item_attributes = {"brand": "Vodafone", "brand_wikidata": "Q122141"}
    start_urls = ["https://www.vodafone.gr/service/?type=getStores"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response, **kwargs):
        for store in response.json():
            store["telephone"] = store["telephone"].replace(",", ";")
            store["website"] = urljoin("https://www.vodafone.gr", store.pop("path"))
            item = DictParser.parse(store)
            item["street_address"] = store["address_name"]
            oh = OpeningHours()
            for rule in store["workingHours"]:
                if rule["hours"] == "Κλειστό":  # closed
                    continue
                day = sanitise_day(rule["day"], DAYS_GR)
                if not day:
                    continue
                for open_time, close_time in re.findall(
                    r"(\d\d:\d\d)\s*-\s*(\d\d:\d\d)", rule["hours"].replace(".", ":")
                ):
                    oh.add_range(day, open_time, close_time)
            item["opening_hours"] = oh

            yield item
