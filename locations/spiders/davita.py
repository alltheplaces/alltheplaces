# -*- coding: utf-8 -*-
import re

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


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


class DavitaSpider(scrapy.Spider):
    name = "davita"
    item_attributes = {"brand": "DaVita"}
    allowed_domains = ["davita.com"]
    start_urls = ("https://www.davita.com/tools/find-dialysis-center",)

    def parse(self, response):
        for state in STATES:
            url = f"https://www.davita.com/api/find-a-center?location={state}&p=1&lat=32.3182314&lng=-86.902298"
            yield scrapy.Request(url, callback=self.parse_locations)

    def parse_locations(self, response):
        data = response.json()
        for location in data.get("locations", []) or []:
            properties = {
                "name": location["facilityname"],
                "ref": location["facilityid"],
                "addr_full": location["address"]["address1"],
                "city": location["address"]["city"],
                "state": location["address"]["state"],
                "postcode": location["address"]["zip"],
                "phone": location.get("phone"),
                "website": "https://davita.com/locations/{}".format(
                    location["facilityid"]
                ),
                "lat": float(location["address"]["latitude"]),
                "lon": float(location["address"]["longitude"]),
            }

            yield GeojsonPointItem(**properties)
