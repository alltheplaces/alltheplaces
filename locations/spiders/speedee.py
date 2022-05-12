# -*- coding: utf-8 -*-
import json
import re

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours

# source: https://gist.github.com/rogerallen/1583593
us_state_to_abbrev = {
    "Alabama": "AL",
    "Alaska": "AK",
    "Arizona": "AZ",
    "Arkansas": "AR",
    "California": "CA",
    "Colorado": "CO",
    "Connecticut": "CT",
    "Delaware": "DE",
    "Florida": "FL",
    "Georgia": "GA",
    "Hawaii": "HI",
    "Idaho": "ID",
    "Illinois": "IL",
    "Indiana": "IN",
    "Iowa": "IA",
    "Kansas": "KS",
    "Kentucky": "KY",
    "Louisiana": "LA",
    "Maine": "ME",
    "Maryland": "MD",
    "Massachusetts": "MA",
    "Michigan": "MI",
    "Minnesota": "MN",
    "Mississippi": "MS",
    "Missouri": "MO",
    "Montana": "MT",
    "Nebraska": "NE",
    "Nevada": "NV",
    "New Hampshire": "NH",
    "New Jersey": "NJ",
    "New Mexico": "NM",
    "New York": "NY",
    "North Carolina": "NC",
    "North Dakota": "ND",
    "Ohio": "OH",
    "Oklahoma": "OK",
    "Oregon": "OR",
    "Pennsylvania": "PA",
    "Rhode Island": "RI",
    "South Carolina": "SC",
    "South Dakota": "SD",
    "Tennessee": "TN",
    "Texas": "TX",
    "Utah": "UT",
    "Vermont": "VT",
    "Virginia": "VA",
    "Washington": "WA",
    "West Virginia": "WV",
    "Wisconsin": "WI",
    "Wyoming": "WY",
    "District of Columbia": "DC",
    "American Samoa": "AS",
    "Guam": "GU",
    "Northern Mariana Islands": "MP",
    "Puerto Rico": "PR",
    "United States Minor Outlying Islands": "UM",
    "U.S. Virgin Islands": "VI",
}


class SpeeDeeSpider(scrapy.Spider):
    name = "speedee_oil"
    item_attributes = {"brand": "SpeeDee Oil Change and Auto Service"}
    allowed_domains = ["speedeeoil.com"]
    custom_settings = {"ROBOTSTXT_OBEY": False}
    start_urls = [
        "https://www.speedeeoil.com/wp-admin/admin-ajax.php?action=asl_load_stores&nonce=207e81f157&load_all=1&layout=1",
    ]

    def parse(self, response):
        for store in response.json():
            if len(store["state"]) == 2:
                state = store["state"]
            else:
                state = us_state_to_abbrev[store["state"]]

            properties = {
                "ref": store["title"].split()[-1],
                "name": store["title"],
                "addr_full": store["street"],
                "city": store["city"],
                "state": state,
                "postcode": store["postal_code"],
                "country": "US",
                "lat": store["lat"],
                "lon": store["lng"],
                "phone": store["phone"],
                "website": store["website"],
            }
            yield GeojsonPointItem(**properties)
