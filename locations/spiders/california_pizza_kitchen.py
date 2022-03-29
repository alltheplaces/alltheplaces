# -*- coding: utf-8 -*-
import re
import scrapy
from locations.items import GeojsonPointItem
from locations.hours import OpeningHours
from urllib.parse import urlencode

STATES = [
    "AL",
    "AK",
    "AZ",
    "AR",
    "CA",
    "CO",
    "CT",
    "DC",
    "DE",
    "FL",
    "GA",
    "HI",
    "ID",
    "IL",
    "IN",
    "IA",
    "KS",
    "KY",
    "LA",
    "ME",
    "MD",
    "MA",
    "MI",
    "MN",
    "MS",
    "MO",
    "MT",
    "NE",
    "NV",
    "NH",
    "NJ",
    "NM",
    "NY",
    "NC",
    "ND",
    "OH",
    "OK",
    "OR",
    "PA",
    "RI",
    "SC",
    "SD",
    "TN",
    "TX",
    "UT",
    "VT",
    "VA",
    "WA",
    "WV",
    "WI",
    "WY",
]

DAY_MAPPING = {
    "1": "Mo",
    "2": "Tu",
    "3": "We",
    "4": "Th",
    "5": "Fr",
    "6": "Sa",
    "7": "Su",
}


class cpkSpider(scrapy.Spider):
    download_delay = 0.2
    name = "cpk"
    item_attributes = {
        "brand": "California Pizza Kitchen",
        "brand_wikidata": "Q15109854",
    }
    allowed_domains = ["momentfeed-prod.apigee.net"]

    def start_requests(self):
        base_url = "https://momentfeed-prod.apigee.net/api/llp.json?"

        for state in STATES:
            params = {
                "auth_token": "CYQKJJAYDMERQLLE",
                "country": "US",
                "region": "{}".format(state),
                "pageSize": "1000",
            }
            yield scrapy.http.Request(base_url + urlencode(params), callback=self.parse)

    def parse(self, response):
        store_data = response.json()

        # States without a store return a dict with a message, otherwise a list of stores as json arrays
        if isinstance(store_data, list):

            for store in store_data:

                properties = {
                    "addr_full": store["store_info"]["address"],
                    "city": store["store_info"]["locality"],
                    "state": store["store_info"]["region"],
                    "postcode": store["store_info"]["postcode"],
                    "country": store["store_info"]["country"],
                    "ref": store["store_info"]["corporate_id"],
                    "website": store["store_info"]["website"],
                    "lat": store["store_info"]["latitude"],
                    "lon": store["store_info"]["longitude"],
                    "name": store["store_info"]["name"],
                }

                store_hours = self.parse_hours(store["store_info"]["store_hours"])

                if store_hours:
                    properties["opening_hours"] = store_hours

                yield GeojsonPointItem(**properties)

    def parse_hours(self, hours):

        if hours != "":

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
