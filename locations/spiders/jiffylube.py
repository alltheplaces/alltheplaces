# -*- coding: utf-8 -*-
import json

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


STATES = [
    "AL",
    "AK",
    "AS",
    "AZ",
    "AR",
    "CA",
    "CO",
    "CT",
    "DE",
    "DC",
    "FM",
    "FL",
    "GA",
    "GU",
    "HI",
    "ID",
    "IL",
    "IN",
    "IA",
    "KS",
    "KY",
    "LA",
    "ME",
    "MH",
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
    "MP",
    "OH",
    "OK",
    "OR",
    "PW",
    "PA",
    "PR",
    "RI",
    "SC",
    "SD",
    "TN",
    "TX",
    "UT",
    "VT",
    "VI",
    "VA",
    "WA",
    "WV",
    "WI",
    "WY",
]

DAY_MAPPING = {
    "Monday": "Mo",
    "Tuesday": "Tu",
    "Wednesday": "We",
    "Thursday": "Th",
    "Friday": "Fr",
    "Saturday": "Sa",
    "Sunday": "Su",
}


class JiffyLubeSpider(scrapy.Spider):
    name = "jiffylube"
    item_attributes = {"brand": "Jiffy Lube", "brand_wikidata": "Q6192247"}
    allowed_domains = ["www.jiffylube.com"]
    start_urls = ("https://www.jiffylube.com/api/locations",)

    def parse(self, response):
        stores = json.loads(response.text)

        for store in stores:
            store_url = "https://www.jiffylube.com/api" + store["_links"]["_self"]
            yield scrapy.Request(store_url, callback=self.parse_store)

    def parse_store(self, response):
        store_data = json.loads(response.text)

        properties = {
            "ref": store_data["id"],
            "addr_full": store_data["address"],
            "city": store_data["city"],
            "state": store_data["state"],
            "postcode": store_data["postal_code"].strip(),
            "country": store_data["country"],
            "phone": store_data["phone_main"],
            "lat": float(store_data["coordinates"]["latitude"]),
            "lon": float(store_data["coordinates"]["longitude"]),
            "website": "https://www.jiffylube.com{}".format(
                store_data["_links"]["_self"]
            ),
        }

        yield GeojsonPointItem(**properties)
