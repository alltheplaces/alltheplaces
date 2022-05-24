# -*- coding: utf-8 -*-
import scrapy

from locations.items import GeojsonPointItem

DAYS = [
    "Su",
    "Mo",
    "Tu",
    "We",
    "Th",
    "Fr",
    "Sa",
]


class RedLobsterSpider(scrapy.Spider):
    name = "redlobster"
    item_attributes = {"brand": "Red Lobster", "brand_wikidata": "Q846301"}
    allowed_domains = ["redlobster.com"]
    start_urls = (
        "https://www.redlobster.com/api/location/GetLocations?latitude=38.9072&longitude=-77.0369&radius=150000",
    )

    def normalize_time(self, time_str):
        time, ampm = time_str.split(" ")
        hour, minute = time.split(":")

        hour = int(hour)
        if ampm == "PM":
            hour = hour + 12

        return "%02d:%s" % (hour, minute)

    def store_hours(self, hours):
        day_groups = []
        this_day_group = None
        for day_info in hours:
            day = DAYS[day_info["dayOfWeek"]]

            hours = "{}-{}".format(
                self.normalize_time(day_info["open"]),
                self.normalize_time(day_info["close"]),
            )

            if not this_day_group:
                this_day_group = {"from_day": day, "to_day": day, "hours": hours}
            elif this_day_group["hours"] != hours:
                day_groups.append(this_day_group)
                this_day_group = {"from_day": day, "to_day": day, "hours": hours}
            elif this_day_group["hours"] == hours:
                this_day_group["to_day"] = day

        day_groups.append(this_day_group)

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
                elif day_group["from_day"] == "Su" and day_group["to_day"] == "Sa":
                    opening_hours += "{hours}; ".format(**day_group)
                else:
                    opening_hours += "{from_day}-{to_day} {hours}; ".format(**day_group)
            opening_hours = opening_hours[:-2]

        return opening_hours

    def parse(self, response):
        results = response.json()
        for result in results["locations"]:
            location = result["location"]
            properties = {
                "addr_full": location["address1"],
                "city": location["city"],
                "state": location["state"],
                "postcode": location["zip"],
                "phone": location["phone"],
                "opening_hours": self.store_hours(location["hours"]),
                "website": "https://www.redlobster.com/locations/list/"
                + location["localPageURL"],
                "ref": location["rlid"],
                "lon": location["longitude"],
                "lat": location["latitude"],
            }

            yield GeojsonPointItem(**properties)
