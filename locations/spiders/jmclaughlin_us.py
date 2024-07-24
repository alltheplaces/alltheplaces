import json
import re

import scrapy
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class JmclaughlinUSSpider(scrapy.Spider):
    name = "jmclaughlin_us"
    item_attributes = {"brand": "J. McLaughlin", "brand_wikidata": "Q111230943"}
    allowed_domains = ["orders.jmclaughlin.com"]

    def start_requests(self):
        yield JsonRequest(
            url="https://orders.jmclaughlin.com/searchForStores",
            data={},
        )

    def parse(self, response):
        raw_text = response.text[1 : len(response.text) - 1]
        raw_text = raw_text.replace('\\"', '"')
        response_json = json.loads(raw_text)
        for start_index in range(0, len(list(response_json["SupplierNames"].keys())), 25):
            supplier_ids = ",".join(list(response_json["SupplierNames"].keys())[start_index : start_index + 25])
            yield JsonRequest(
                url="https://orders.jmclaughlin.com/loadStoresBySupplierIds",
                data={
                    "supplierIds": supplier_ids,
                },
                callback=self.parse_stores,
            )

    def parse_stores(self, response):
        raw_text = response.text[1 : len(response.text) - 1]
        raw_text = raw_text.replace('\\"', '"')
        raw_text = raw_text.replace("\\/", "/")
        response_json = json.loads(raw_text)
        for n in response_json:
            location = response_json[n]
            item = DictParser.parse(location)
            item["ref"] = location["SupplierId"]
            item["lat"] = location["MetaData"]["Geometry"]["location"]["lat"]
            item["lon"] = location["MetaData"]["Geometry"]["location"]["lng"]
            item["website"] = "https://www.jmclaughlin.com/store-details?store=" + "/".join(
                [
                    location["StoreIdentifier"]["CountryUrl"],
                    location["StoreIdentifier"]["StateUrl"],
                    location["StoreIdentifier"]["CityUrl"],
                    location["StoreIdentifier"]["Address1Url"],
                    location["StoreIdentifier"]["SupplierNameUrl"],
                ]
            )

            oh = OpeningHours()
            for day in "Sun", "Mon", "Tues", "Wed", "Thurs", "Fri", "Sat":
                for start_hour, start_min, start_am_pm, end_hour, end_min, end_am_pm in re.findall(
                    r"(\d{1,2})(?:[:\.](\d{2}))?\s*(AM|PM)\s*-\s*(\d{1,2})(?:[:\.](\d{2}))?\s*(AM|PM)",
                    location[day],
                    flags=re.IGNORECASE,
                ):
                    if len(start_hour) == 1:
                        start_hour = "0" + start_hour
                    if len(end_hour) == 1:
                        end_hour = "0" + end_hour
                    if start_min == "":
                        start_min = "00"
                    if end_min == "":
                        end_min = "00"
                    start_time = f"{start_hour}:{start_min} {start_am_pm}"
                    end_time = f"{end_hour}:{end_min} {end_am_pm}"
                    oh.add_range(day, start_time, end_time, time_format="%I:%M %p")
            item["opening_hours"] = oh.as_opening_hours()

            yield item
