import json
import re

import scrapy
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours


class TerryWhiteChemmartAUSpider(scrapy.Spider):
    name = "terry_white_chemmart_au"
    item_attributes = {
        "brand": "Terry White Chemmart",
        "brand_wikidata": "Q24089773",
        "country": "AU",
    }
    allowed_domains = ["terrywhitechemmart.com.au"]
    requires_proxy = True

    def start_requests(self):
        yield JsonRequest(
            url="https://terrywhitechemmart.com.au/store-api/get-stores-summary",
            data={},
            method="POST",
        )

    def parse(self, response):
        stores = json.loads(response.body)
        for store in stores["data"]:
            item = DictParser.parse(store)
            item["ref"] = store["sharedStoreIdentifier"]
            item["city"] = store["suburb"]

            if "addressLine1" in item and "addressLine2" in item:
                item["street_address"] = ", ".join([store["addressLine1"], store["addressLine2"]])

            item["website"] = "https://terrywhitechemmart.com.au/stores/" + store["storeSlug"]

            item["opening_hours"] = OpeningHours()
            for day in DAYS:
                for start_time, end_time in re.findall(
                    day + r"(?:(\d{4})(\d{4})|X{8})",
                    store["availability"],
                    flags=re.IGNORECASE,
                ):
                    if start_time != "" and end_time != "":
                        item["opening_hours"].add_range(day, start_time, end_time, time_format="%H%M")
            yield (item)
