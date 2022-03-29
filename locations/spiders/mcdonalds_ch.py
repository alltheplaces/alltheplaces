# -*- coding: utf-8 -*-
import scrapy
import re
import datetime
from locations.items import GeojsonPointItem


class McDonalsCHSpider(scrapy.Spider):

    name = "mcdonalds_ch"
    item_attributes = {"brand": "McDonald's"}
    allowed_domains = ["www.mcdonalds.ch"]
    start_urls = (
        "https://www.mcdonalds.ch/api/v1/restaurants/?lon=7.458354699999973&lat=46.786249&range=1000",
        "https://www.mcdonalds.ch/api/v1/restaurants/?lon=9.022665800000027&lat=46.9342272&range=1000",
    )

    def normalize_time(self, time_str):
        time = datetime.datetime.fromtimestamp(time_str).strftime("%H:%M %Z%z")
        return time

    def store_hours(self, data):
        day_groups = []
        this_day_group = {}
        day_hours = data["dayofweekservice"]
        for day_hour in day_hours:
            if not day_hour["isOpen"]:
                continue
            hours = ""
            day, start, end = (
                day_hour["dayOfWeek"],
                day_hour["startTime"],
                day_hour["endTime"],
            )
            start = self.normalize_time(start)
            end = self.normalize_time(end)

            short_day = day[:2]
            hours = "{}:{}-{}:{}".format(start[:2], start[3:], end[:2], end[3:])
            if not this_day_group:
                this_day_group = {
                    "from_day": short_day,
                    "to_day": short_day,
                    "hours": hours,
                }

            elif hours == this_day_group["hours"]:
                this_day_group["to_day"] = short_day

            elif hours != this_day_group["hours"]:
                day_groups.append(this_day_group)
                this_day_group = {
                    "from_day": short_day,
                    "to_day": short_day,
                    "hours": hours,
                }

        day_groups.append(this_day_group)

        if not day_groups:
            return None
        if not day_groups[0]:
            return None
        opening_hours = ""
        if len(day_groups) == 1 and day_groups[0]["hours"] in (
            "00:00-23:59",
            "00:00-00:00",
        ):
            opening_hours = "24/7"
        else:
            for day_group in day_groups:
                if day_group["from_day"] == day_group["to_day"]:
                    opening_hours += "{from_day} {hours}; ".format(**day_group)
                else:
                    opening_hours += "{from_day}-{to_day} {hours}; ".format(**day_group)
            opening_hours = opening_hours[:-2]

        return opening_hours

    def parse(self, response):
        results = response.json()
        for data in results:
            properties = {
                "city": data["address"]["cityTown"],
                "ref": data["id"],
                "addr_full": data["address"]["addressLine1"],
                "phone": data["storeNumbers"]["phonenumber"][0]["number"],
                "state": data["address"]["country"],
                "postcode": data["address"]["postalZip"],
                "lat": data["address"]["location"]["lat"],
                "lon": data["address"]["location"]["lon"],
                "name": data["publicName"],
            }

            opening_hours = self.store_hours(data["storeServices"])
            if opening_hours:
                properties["opening_hours"] = opening_hours

            yield GeojsonPointItem(**properties)
