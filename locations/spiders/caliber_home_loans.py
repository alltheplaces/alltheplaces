# -*- coding: utf-8 -*-
import json

import scrapy

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


class CaliberHomeLoansSpider(scrapy.Spider):
    name = "caliber_home_loans"
    item_attributes = {"brand": "Caliber Home Loans", "brand_wikidata": "Q25055134"}
    allowed_domains = ["www.caliberhomeloans.com"]
    download_delay = 0.3

    def start_requests(self):
        url = "https://www.caliberhomeloans.com/Home/BranchList?stateCode={state}&LCSpeciality=all&SpanishSpeaking=no"

        for state in STATES:
            yield scrapy.http.Request(
                method="GET", url=url.format(state=state), callback=self.parse_state
            )

    def parse_state(self, response):
        data = json.loads(response.text)

        if data:
            for store in data:

                properties = {
                    "ref": store["BranchID"],
                    "name": store["Name"],
                    "addr_full": store["Address"],
                    "city": store["City"],
                    "state": store["State"],
                    "postcode": store["ZipCode"],
                    "lat": store["Latitude"],
                    "lon": store["Longitude"],
                    "website": response.url,
                }

                yield GeojsonPointItem(**properties)
