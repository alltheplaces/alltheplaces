# -*- coding: utf-8 -*-
import scrapy
from urllib.parse import urlencode
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

BASE_URL = "https://shop.harborfreight.com/storelocator/location/state?"


class HarborFreightSpider(scrapy.Spider):
    name = "harborfreight"
    item_attributes = {"brand": "Harbor Freight"}
    allowed_domains = ["harborfreight.com"]
    start_urls = ("https://www.harborfreight.com/storelocator/location/map",)
    download_delay = 0.2

    def parse(self, response):
        for state in STATES:
            params = {
                "state": "{}".format(state),
                "justState": "true",
                "stateValue": "{}".format(state),
            }

            yield scrapy.http.Request(
                BASE_URL + urlencode(params), callback=self.parse_stores
            )

    def parse_stores(self, response):
        stores = response.xpath(".//marker")
        for store in stores:
            properties = {
                "ref": store.xpath("@location_id").extract_first(),
                "name": store.xpath("@title").extract_first(),
                "addr_full": store.xpath("@address").extract_first(),
                "city": store.xpath("@city").extract_first(),
                "state": store.xpath("@state").extract_first(),
                "postcode": store.xpath("@zip").extract_first(),
                "lat": store.xpath("@latitude").extract_first(),
                "lon": store.xpath("@longitude").extract_first(),
                "phone": store.xpath("@phone").extract_first(),
                "website": response.url,
            }

            yield GeojsonPointItem(**properties)
