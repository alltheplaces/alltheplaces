import json
import re

import scrapy

from locations.hours import DAYS_EN, OpeningHours
from locations.items import Feature


class INGBankNLSpider(scrapy.Spider):
    name = "ing_bank_nl"
    start_urls = ["https://api.www.ing.nl/locator/offices?country=NL&lang=nl"]

    item_attributes = {"brand": "ING Bank", "brand_wikidata": "Q645708"}
    custom_settings = {
        "ROBOTSTXT_OBEY": False,
    }

    def parse(self, response, **kwargs):
        for store in response.json().get("locations"):
            address_details = store.get("address")
            yield scrapy.Request(
                f"https://api.www.ing.nl/locator/offices/{store.get('id')}",
                callback=self.parse_store,
                meta={
                    "housenumber": address_details.get("number"),
                    "street": address_details.get("street"),
                    "postcode": address_details.get("postalCode"),
                    "city": address_details.get("city"),
                    "street_address": ", ".join([address_details.get("number"), address_details.get("street")]),
                    "lat": store.get("latitude"),
                    "lon": store.get("longitude"),
                    "name": store.get("name"),
                },
            )

    def parse_store(self, response):
        store = response.json()
        oh = OpeningHours()
        for hours in store.get("timetable").get("office"):
            if not hours.get("hours"):
                continue
            for day_hours in hours.get("hours"):
                oh.add_range(
                    DAYS_EN.get(hours.get("day").capitalize()),
                    day_hours.get("open"),
                    day_hours.get("closed"),
                )
        yield Feature(
            {
                "ref": store.get("id"),
                "name": response.meta.get("name"),
                "street": response.meta.get("street"),
                "housenumber": response.meta.get("housenumber"),
                "postcode": response.meta.get("postcode"),
                "city": response.meta.get("city"),
                "street_address": response.meta.get("street_address"),
                "country": store.get("country"),
                "email": store.get("email"),
                "phone": store.get("phone"),
                "lat": response.meta.get("lat"),
                "lon": response.meta.get("lon"),
                "opening_hours": oh,
            }
        )
