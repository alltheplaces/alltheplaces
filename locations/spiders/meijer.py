# -*- coding: utf-8 -*-
import scrapy
import json
import re
from locations.items import GeojsonPointItem

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


class MeijerSpider(scrapy.Spider):
    name = "meijer"
    item_attributes = {"brand": "Meijer"}
    allowed_domains = ["www.meijer.com"]

    def start_requests(self):
        for state in STATES:
            yield scrapy.Request(
                "https://www.meijer.com/custserv/locate_store_by_state.cmd?form_state=locateStoreByStateForm&state={}".format(
                    state
                ),
                callback=self.parse,
            )

    def parse(self, response):
        stores = response.css("div.records_inner>script::text").extract_first()

        if stores:
            stores = stores.strip()[13:-1]
            stores = stores.replace("','", '","')
            stores = stores.replace("['", '["')
            stores = stores.replace("']", '"]')
            stores = json.loads(stores)
            loc_data = response.css("script").extract()[10]
            lat_matches = re.findall(
                r"(\"LAT\"), (\")([+-]?([0-9]*[.])?[0-9]+)(\")", loc_data
            )
            lon_matches = re.findall(
                r"(\"LNG\"), (\")([+-]?([0-9]*[.])?[0-9]+)(\")", loc_data
            )

            n = 0
            for store in stores:
                address1 = store[6].split(",")
                city = address1[0].strip()
                address2 = address1[1].strip().split(" ")
                state = address2[0]
                postcode = address2[1]
                properties = {
                    "ref": store[0],
                    "name": store[1],
                    "phone": store[7],
                    "opening_hours": self.hours(store[8]),
                    "lat": lat_matches[n][2],
                    "lon": lon_matches[n][2],
                    "street": store[2],
                    "city": city,
                    "state": state,
                    "postcode": postcode,
                }

                n = n + 1

                yield GeojsonPointItem(**properties)

    def hours(self, data):
        if data == "Open 24 hrs a day, 364 days a year.":
            return "24/7"
        else:
            return data
