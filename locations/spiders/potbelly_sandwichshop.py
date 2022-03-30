# -*- coding: utf-8 -*-
import scrapy
import json
import re

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class PotbellySandwichSpider(scrapy.Spider):

    name = "potbelly_sandwich"
    item_attributes = {"brand": "Potbelly Sandwich Shop"}
    allowed_domains = ["www.potbelly.com"]
    start_urls = (
        "https://api-potbelly-production.fuzzstaging.com/proxy/all-locations",
    )

    def parse(self, response):
        results = response.text
        locations = json.loads(results)

        for data in locations:
            properties = {
                "ref": data["location"]["id"],
                "name": data["location"]["name"],
                "lat": data["location"]["latitude"],
                "lon": data["location"]["longitude"],
                "addr_full": data["location"]["street_address"],
                "city": data["location"]["locality"],
                "state": data["location"]["region"],
                "postcode": data["location"]["postal_code"],
                "phone": data["location"]["phone"],
                "website": "https://www.potbelly.com/stores/%s"
                % data["location"]["id"],
            }

            hours = json.loads(data["location"]["meta"]["open_hours"])
            if hours:
                oh = OpeningHours()
                for d, v in hours.items():
                    for r in v:
                        open_time = r["opens_at"]
                        close_time = r["closes_at"]
                        oh.add_range(d[:2], open_time, close_time, "%H:%M:%S")
                properties["opening_hours"] = oh.as_opening_hours()

            yield GeojsonPointItem(**properties)
