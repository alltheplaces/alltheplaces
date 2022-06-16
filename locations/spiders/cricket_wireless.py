# -*- coding: utf-8 -*-
import re

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours

DAY_MAPPING = {
    "1": "Mo",
    "2": "Tu",
    "3": "We",
    "4": "Th",
    "5": "Fr",
    "6": "Sa",
    "7": "Su",
}


class CricketWirelessSpider(scrapy.Spider):
    name = "cricket_wireless"
    item_attributes = {"brand": "Cricket Wireless", "brand_wikidata": "Q5184987"}
    allowed_domains = ["api.momentfeed.com"]

    def get_page(self, n):
        url = f"https://api.momentfeed.com/v1/analytics/api/llp/cricket.json?pageSize=100&page={n}"
        return scrapy.Request(
            url, headers={"Authorization": "IVNLPNUOBXFPALWE"}, meta={"page": n}
        )

    def start_requests(self):
        yield self.get_page(1)

    def parse(self, response):
        data = response.json()
        if "message" in data:
            # End of results
            return
        for row in data:
            store = row["store_info"]
            properties = {
                "lat": store["latitude"],
                "lon": store["longitude"],
                "ref": store["corporate_id"],
                "website": store["website"],
                "name": store["name"],
                "street_address": store["address"],
                "city": store["locality"],
                "state": store["region"],
                "postcode": store["postcode"],
                "phone": store["phone"],
                "opening_hours": self.parse_hours(store["store_hours"]),
            }
            yield GeojsonPointItem(**properties)
        yield self.get_page(1 + response.meta["page"])

    def parse_hours(self, hours):
        if hours not in ["", ";"]:
            opening_hours = OpeningHours()
            hour_list = hours.strip(";").split(";")
            for hour in hour_list:
                day, open_time, close_time = re.search("(.),(.+),(.+)", hour).groups()
                opening_hours.add_range(
                    day=DAY_MAPPING[day],
                    open_time=open_time[0:2] + ":" + open_time[2:4],
                    close_time="23:59"
                    if (close_time[0:2] + ":" + close_time[2:4]) == "24:00"
                    else close_time[0:2] + ":" + close_time[2:4],
                )
            return opening_hours.as_opening_hours()
