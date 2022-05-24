# -*- coding: utf-8 -*-
import re
import datetime

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours

DAYS_NAME = {
    "Monday": "Mo",
    "Tuesday": "Tu",
    "Wednesday": "We",
    "Thursday": "Th",
    "Friday": "Fr",
    "Saturday": "Sa",
    "Sunday": "Su",
}


class TheKegSteakhouseSpider(scrapy.Spider):
    name = "the_keg_steakhouse"
    item_attributes = {"brand": "The Keg Steakhouse", "brand_wikidata": "Q7744066"}
    allowed_domains = ["kegsteakhouse.com"]
    start_urls = [
        "https://kegsteakhouse.com/en/location/list",
    ]

    def parse_hours(self, hours):
        opening_hours = OpeningHours()

        for hour in hours:
            day = DAYS_NAME[hour]
            opening = hours[hour][0]["opening"]
            closing = hours[hour][0]["closing"]

            open_time = datetime.datetime.strptime(opening, "%I:%M%p").strftime("%H:%M")
            close_time = datetime.datetime.strptime(closing, "%I:%M%p").strftime(
                "%H:%M"
            )

            opening_hours.add_range(
                day=day, open_time=open_time, close_time=close_time, time_format="%H:%M"
            )

        return opening_hours.as_opening_hours()

    def parse(self, response):
        places = response.json()

        for place in places:
            properties = {
                "ref": place["singleplatform"]["location_nid"],
                "name": place["singleplatform"]["name"],
                "addr_full": place["singleplatform"]["location"]["address1"],
                "city": place["singleplatform"]["location"]["city"],
                "state": place["singleplatform"]["location"]["state"],
                "postcode": place["singleplatform"]["location"]["postal_code"],
                "country": place["singleplatform"]["location"]["country"],
                "lat": place["singleplatform"]["location"]["latitude"],
                "lon": place["singleplatform"]["location"]["longitude"],
                "phone": place["singleplatform"]["phone"],
                "website": place["singleplatform"]["website"],
            }

            if place["singleplatform"]["has_hours"] == False:
                pass
            else:
                h = self.parse_hours(place["singleplatform"]["hours"])
                if h:
                    properties["opening_hours"] = h

            yield GeojsonPointItem(**properties)
