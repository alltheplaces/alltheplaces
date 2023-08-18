# -*- coding: utf-8 -*-

import scrapy

from locations.hours import OpeningHours
from locations.items import Feature


class MaggianosLittleItalySpider(scrapy.Spider):
    name = "maggianos_little_italy"
    item_attributes = {"brand": "Maggiano's Little Italy", "brand_wikidata": "Q6730149"}
    allowed_domains = ["maggianos.com"]
    start_urls = [
        "https://www.maggianos.com/api//restaurant-data/",
    ]

    def parse_hours(self, hours):
        opening_hours = OpeningHours()

        for hour in hours:
            day = hour["day_name"][:2]
            opening_hours.add_range(day, open_time=hour["open_time"], close_time=hour["end_time"])

        return opening_hours

    def parse(self, response):
        data = response.json()

        for place in data:
            properties = {
                "name": place["properties"]["business_name"],
                "ref": place["properties"]["store_code"],
                "addr_full": place["properties"]["full_address"],
                "street_address": place["properties"]["slug"]["address_line_1"],
                "city": place["properties"]["slug"]["city"],
                "state": place["properties"]["slug"]["state_abbreviation"],
                "postcode": place["properties"]["slug"]["postal_code"],
                "country": place["properties"]["country"],
                "phone": place["properties"]["primary_phone"],
                "lat": place["geometry"]["coordinates"]["latitude"],
                "lon": place["geometry"]["coordinates"]["longitude"],
            }

            properties["opening_hours"] = self.parse_hours(place["properties"]["store_hours"])

            yield Feature(**properties)
