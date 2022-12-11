import re

import scrapy
from scrapy.utils.request import request_fingerprint

from locations.items import GeojsonPointItem


class AndPizzaSpider(scrapy.Spider):
    name = "andpizza"
    item_attributes = {"brand": "&pizza", "brand_wikidata": "Q21189222"}
    start_urls = ("https://api.andpizza.com/webapi/v100/partners/shops",)
    custom_settings = {
        "REQUEST_FINGERPRINTER_IMPLEMENTATION": "2.7",
        "ROBOTSTXT_OBEY": False,
    }

    def start_requests(self):

        url = self.start_urls[0]

        headers = {
            "Accept": "application/json, text/plain, */*",
            "Referer": "https://order.andpizza.com/",
            "Connection": "keep-alive",
            "Authorization": "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOjIsInBhcnRuZXIiOiJpNzIiLCJpc3MiOiJodHRwczovL2FwaS5hbmRwaXp6YS5jb20iLCJpYXQiOjE1OTgyOTEwNzUsImV4cCI6MTkxMzY1MTA3NSwibmJmIjoxNTk4MjkxMDc1LCJqdGkiOiI4VWh1VnhJRjFwZFhrSXplIn0.rXJL4rt5YbT4XRk21sSrkoGffJ5ttowV3UbHInZcnMs",
        }

        yield scrapy.Request(url=url, headers=headers, callback=self.parse)

    def normalize_time(sef, time_str):
        match = re.search(r"([0-9]{1,2}):([0-9]{2}) (a|p)m$", time_str)
        if not match:
            match = re.search(r"([0-9]{1,2}):([0-9]{2})(a|p)m$", time_str)
            h, m, am_pm = match.groups()
        else:
            h, m, am_pm = match.groups()

        return "%02d:%02d" % (
            int(h) + 12 if am_pm == "p" else int(h),
            int(m),
        )

    def parse_hours(self, data):
        opening_hours = ""

        for i in range(len(data)):
            days = data[i]["label"].split(" - ")
            hours = data[i]["value"]
            if len(days) == 1:
                day = days[0][:2]
            elif len(days) == 2:
                day = days[0][:2] + "-" + days[1][:2]
            else:
                day = "Mo-Su"

            hours = hours.split(" - ")
            open = self.normalize_time(hours[0].strip())
            close = self.normalize_time(hours[1].strip())

            open_close = "{}-{}".format(open, close)

            opening_hours += "{} {}; ".format(day, open_close)

        return opening_hours

    def parse(self, response):

        stores = response.json().get("data")
        for store in stores:
            props = {}
            props["name"] = store["name"]
            props["ref"] = store["id"]
            props["addr_full"] = store["location"]["address1"]
            props["city"] = store["location"]["city"]
            props["state"] = store["location"]["state"]
            props["lat"] = store["location"]["latitude"]
            props["lon"] = store["location"]["longitude"]
            props["postcode"] = store["location"]["zipcode"]
            props["phone"] = store["location"]["phone"]

            props["opening_hours"] = self.parse_hours(store["service_schedule"]["general"])

            yield GeojsonPointItem(**props)
