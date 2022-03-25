# -*- coding: utf-8 -*-
import scrapy
import json

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class CompleteCashSpider(scrapy.Spider):
    name = "completecash"
    item_attributes = {"brand": "Complete Cash"}
    allowed_domains = ["locations.completecash.net"]
    cc_url = "https://locations.completecash.net/api/5c1bc42410e9b07c77f0fab5/locations-details"
    base_url = "https://locations.completecash.net/"

    start_urls = (cc_url,)

    def get_opening_hours(self, days):
        o = OpeningHours()
        for day, hours in days.items():
            short_day = day[:2]
            if hours:
                hours = hours[0]
                o.add_range(short_day, hours[0], hours[1])
        return o.as_opening_hours()

    def parse_location(self, location):
        properties = location["properties"]
        opening_hours = self.get_opening_hours(properties["hoursOfOperation"])
        coordinates = location["geometry"]["coordinates"]

        props = {
            "addr_full": properties["addressLine1"] + "\n" + properties["addressLine2"],
            "lat": coordinates[1],
            "lon": coordinates[0],
            "city": properties["city"],
            "postcode": properties["postalCode"],
            "state": properties["province"],
            "phone": properties["phoneNumber"],
            "ref": self.base_url + properties["slug"],
            "website": self.base_url + properties["slug"],
            "opening_hours": opening_hours,
        }
        return GeojsonPointItem(**props)

    def parse(self, response):
        locations = json.loads(response.text)["features"]
        for location in locations:
            yield self.parse_location(location)
