# -*- coding: utf-8 -*-
import re

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours
from datetime import datetime

Seven_Days = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]


class CaseysGeneralStoreSpider(scrapy.Spider):
    name = "caseys_general_store"
    item_attributes = {"brand": "Casey's General Store"}
    allowed_domains = ["caseys.com"]

    def start_requests(self):
        headers = {
            "Accept": "application/json",
        }

        base_url = "https://www.caseys.com/store-finder/getStores?occasionType=carryout&latitude={lat}&longitude={lng}"

        with open(
            "./locations/searchable_points/us_centroids_10mile_radius.csv"
        ) as points:
            next(points)
            for point in points:
                _, lat, lon = point.strip().split(",")

                # Max bounds based on the overview map at https://www.caseys.com/store-finder/locations
                if (
                    32 > float(lat)
                    or float(lat) > 50
                    or -104.5 > float(lon)
                    or float(lon) > -80
                ):
                    continue

                url = base_url.format(lat=lat, lng=lon)
                yield scrapy.Request(url=url, headers=headers, callback=self.parse)

    def parse_hours(self, hours):
        opening_hours = OpeningHours()

        for hour in hours:
            operation_times = hour.split(" ")

            if operation_times[0] != "24/7":
                open_time = operation_times[1] + operation_times[2].upper()
                close_time = operation_times[4] + operation_times[5].upper()
                if ":" in open_time:
                    open_time = datetime.strptime(open_time, "%I:%M%p")
                else:
                    open_time = datetime.strptime(open_time, "%I%p").strftime("%H:%M")
                if ":" in close_time:
                    close_time = datetime.strptime(close_time, "%I:%M%p")
                else:
                    close_time = datetime.strptime(close_time, "%I%p").strftime("%H:%M")
            else:
                for day in Seven_Days:
                    opening_hours.add_range(
                        day=day,
                        open_time="00:00",
                        close_time="00:00",
                        time_format="%H:%M",
                    )

            if operation_times[0] == "Mon-Sun":
                for day in Seven_Days:
                    opening_hours.add_range(
                        day=day,
                        open_time=open_time,
                        close_time=close_time,
                        time_format="%H:%M",
                    )

            elif operation_times[0] == "Mon-Fri":
                for day in Seven_Days[:5]:
                    opening_hours.add_range(
                        day=day,
                        open_time=open_time,
                        close_time=close_time,
                        time_format="%H:%M",
                    )

            elif operation_times[0] == "Sat-Sun":
                for day in Seven_Days[5:]:
                    opening_hours.add_range(
                        day=day,
                        open_time=open_time,
                        close_time=close_time,
                        time_format="%H:%M",
                    )

        return opening_hours.as_opening_hours()

    def parse(self, response):
        data = response.json()

        for store in data["stores"]:
            postal = store["address"]["postalCode"]
            postal = postal.split("-")
            amenities = store["amenities"]

            properties = {
                "ref": store["code"],
                "name": store["displayName"],
                "addr_full": store["address"]["line1"],
                "city": store["address"]["town"],
                "state": store["address"]["region"]["isocodeShort"],
                "postcode": postal[0],
                "country": store["address"]["region"]["countryIso"],
                "lat": store["geoPoint"]["latitude"],
                "lon": store["geoPoint"]["longitude"],
                "phone": store["address"]["phone"],
                "website": "https://www.caseys.com" + store["locationUrl"],
                "extras": {
                    "amenity:fuel": True,
                    "car_wash": any("carwash" == a["key"] for a in amenities) or None,
                    "fuel:diesel": any("diesel" == a["key"] for a in amenities) or None,
                    "shop": "convenience",
                },
            }

            try:
                h = self.parse_hours(store["storeOpenHours"])
                if h:
                    properties["opening_hours"] = h
            except:
                pass

            yield GeojsonPointItem(**properties)
