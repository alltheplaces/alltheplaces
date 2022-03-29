# -*- coding: utf-8 -*-
import scrapy
import json

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


class MurphyUSASpider(scrapy.Spider):
    name = "murphy_usa"
    item_attributes = {"brand": "Murphy USA", "brand_wikidata": "Q19604459"}
    allowed_domains = ["murphyusa.com"]

    def start_requests(self):
        for state in STATES:
            yield scrapy.http.JsonRequest(
                "http://locator.murphyusa.com/MapServices.asmx/GetLocations",
                method="POST",
                data={"stateAbbr": state, "filter": None},
                callback=self.fetch_diesel_stores,
            )

    def fetch_diesel_stores(self, response):
        stores = response.json().get("d")

        if len(stores) > 0:
            query = json.loads(response.request.body)
            query.update({"filter": "diesel"})

            yield scrapy.http.JsonRequest(
                "http://locator.murphyusa.com/MapServices.asmx/GetLocations",
                method="POST",
                meta={"stores": stores},
                data=query,
            )

    def parse(self, response):
        stores = response.meta["stores"]
        diesel_stores = response.json().get("d")

        for store in stores:
            properties = {
                "ref": store["StoreNum"],
                "lon": store["Long"],
                "lat": store["Lat"],
                "name": f"Murphy Express #{store['StoreNum']}"
                if store["IsExpress"]
                else f"Murphy USA #{store['StoreNum']}",
                "addr_full": store["Address"],
                "city": store["City"],
                "state": store["State"],
                "postcode": store["Zip"],
                "country": "US",
                "extras": {
                    "amenity:fuel": True,
                    "fuel:diesel": any(
                        d["StoreNum"] == store["StoreNum"] for d in diesel_stores
                    ),
                },
            }

            yield scrapy.http.JsonRequest(
                "http://locator.murphyusa.com/MapServices.asmx/StoreDetailHtml",
                method="POST",
                meta={"item_properties": properties},
                data={"storeNum": int(store["StoreNum"]), "distance": 0},
                callback=self.add_details,
            )

    def add_details(self, response):
        properties = response.meta["item_properties"]
        opening_hours = OpeningHours()

        details_html = response.json().get("d")
        details = scrapy.Selector(text=details_html)

        days = details.css(".hours th::text").getall()
        hours = details.css(".hours td::text").getall()

        for day, hours in zip(days, hours):
            (open_time, close_time) = hours.split()

            opening_hours.add_range(
                day=day[0:2],
                open_time=f"{open_time}M",
                close_time=f"{close_time}M",
                time_format="%I:%M%p",
            )

        properties.update(
            {
                "phone": details.css(".phone::text").get().replace("Phone: ", ""),
                "opening_hours": opening_hours.as_opening_hours(),
            }
        )

        yield GeojsonPointItem(**properties)
