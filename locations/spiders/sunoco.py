# -*- coding: utf-8 -*-
import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class SunocoSpider(scrapy.Spider):
    name = "sunoco"
    item_attributes = {"brand": "Sunoco", "brand_wikidata": "Q1423218"}
    allowed_domains = ["sunoco.com"]

    start_urls = ["https://www.sunoco.com/js/locations.json"]

    def parse(self, response):
        for location in response.json():
            opening_hours = OpeningHours()

            for key, val in location.items():
                if not key.endswith("_Hours"):
                    continue
                day = key[:2].capitalize()
                if val == "24 hours":
                    open_time = close_time = "12 AM"
                else:
                    open_time, close_time = val.split(" to ")
                opening_hours.add_range(day, open_time, close_time, "%I %p")

            yield GeojsonPointItem(
                ref=location["Store_ID"],
                lon=location["Longitude"],
                lat=location["Latitude"],
                # name as shown on the Sunoco site
                name=f"Sunoco #{location['Store_ID']}",
                addr_full=location["Street_Address"],
                city=location["City"],
                state=location["State"],
                postcode=location["Postalcode"],
                country="US",
                phone=location["Phone"],
                opening_hours=opening_hours.as_opening_hours(),
                extras={
                    "amenity:fuel": True,
                    "atm": location["ATM"] == "Y",
                    "car_wash": location["CarWash"],
                    "fuel:diesel": location["HasDiesel"] == "Y",
                    "fuel:kerosene": location["HasKero"] == "Y",
                },
            )
