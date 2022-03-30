# -*- coding: utf-8 -*-
import scrapy
from locations.items import GeojsonPointItem
from locations.hours import OpeningHours
import datetime

Days = ["Mo", "Tu", "We", "Th", "Fr"]


class LidsSpider(scrapy.Spider):
    name = "lids"
    item_attributes = {"brand": "Lids"}
    allowed_domains = ["lids.com"]

    def start_requests(self):
        url = "https://www.lids.com/api/stores?lat=30.2729209&long=-97.74438630000002&num=1200&shipToStore=false"
        yield scrapy.Request(url)

    def parse_hours(self, hours):
        opening_hours = OpeningHours()

        if "monFriOpen" in hours:
            day = "Mo-Fr"
            open_time = datetime.datetime.strptime(
                hours["monFriOpen"], "%H:%M %p"
            ).strftime("%H:%M")
            close_time = datetime.datetime.strptime(
                hours["monFriClose"], "%H:%M %p"
            ).strftime("%H:%M")
            for day in Days:
                opening_hours.add_range(
                    day=day,
                    open_time=open_time,
                    close_time=close_time,
                    time_format="%H:%M",
                )

        if "satOpen" in hours:
            day = "Sa"
            open_time = datetime.datetime.strptime(
                hours["satOpen"], "%H:%M %p"
            ).strftime("%H:%M")
            close_time = datetime.datetime.strptime(
                hours["satClose"], "%H:%M %p"
            ).strftime("%H:%M")
            opening_hours.add_range(
                day=day, open_time=open_time, close_time=close_time, time_format="%H:%M"
            )

        if "sunOpen" in hours:
            day = "Su"
            open_time = datetime.datetime.strptime(
                hours["sunOpen"], "%H:%M %p"
            ).strftime("%H:%M")
            close_time = datetime.datetime.strptime(
                hours["sunClose"], "%H:%M %p"
            ).strftime("%H:%M")
            opening_hours.add_range(
                day=day, open_time=open_time, close_time=close_time, time_format="%H:%M"
            )

        return opening_hours.as_opening_hours()

    def parse(self, response):
        ldata = response.json()

        for row in ldata:

            properties = {
                "ref": row["key"],
                "name": row["name"],
                "addr_full": row["address1"],
                "city": row["city"],
                "postcode": row["zip"],
                "lat": row["latitude"],
                "lon": row["longitude"],
                "phone": row["phone"],
                "state": row["state"],
            }

            # h = ["monFriOpen", "satOpen", "sunOpen", "monFriClose", "satClose", "sunClose"]
            hours = self.parse_hours(row)

            if hours:
                properties["opening_hours"] = hours

            yield GeojsonPointItem(**properties)
