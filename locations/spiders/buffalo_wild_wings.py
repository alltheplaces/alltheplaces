# -*- coding: utf-8 -*-
import re

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class BuffaloWildWingsSpider(scrapy.Spider):
    name = "buffalo_wild_wings"
    item_attributes = {"brand": "Buffalo Wild Wings", "brand_wikidata": "Q509255"}
    allowed_domains = ["buffalowildwings.com"]

    def start_requests(self):
        base_url = "https://api.buffalowildwings.com/BWWService.svc/GetRestaurntDetailsByltdLng?fLatitude={lat}&fLongitude={lon}&radius=500&iVendorID=50"

        HEADERS = {
            "x_client_id": "4171883342bf4b88aa4b88ec77f5702b",
            "x_client_secret": "786c1B856fA542C4b383F3E8Cdd36f3f",
        }

        with open(
            "./locations/searchable_points/us_centroids_50mile_radius.csv"
        ) as points:
            next(points)
            for point in points:
                _, lat, lon = point.strip().split(",")
                url = base_url.format(lat=lat, lon=lon)
                yield scrapy.Request(url=url, headers=HEADERS, callback=self.parse)

    def parse_hours(self, hours):
        opening_hours = OpeningHours()

        days_of_week = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]

        for d in days_of_week:
            try:
                day = d[:-1]
                open_name = "HourOfOperation{0}Open".format(d)
                if d == "Mon":
                    close_name = "HourOfOperation{0}close".format(d)
                else:
                    close_name = "HourOfOperation{0}Close".format(d)
                open_time = hours[open_name]
                close_time = hours[close_name]
            except:
                continue

            opening_hours.add_range(
                day=day,
                open_time=open_time,
                close_time=close_time,
                time_format="%I:%M %p",
            )

        return opening_hours.as_opening_hours()

    def parse(self, response):
        places = response.json()

        for place in places:
            try:
                properties = {
                    "ref": place["RestaurantNumber"],
                    "name": place["LocationName"],
                    "addr_full": place["AddressLine1"],
                    "city": place["City"],
                    "state": place["State"],
                    "postcode": place["PostalCode"],
                    "country": place["Country"],
                    "lat": place["Latitude"],
                    "lon": place["Longitude"],
                    "phone": place["RestaurantPhoneNumber"],
                }

                hours = self.parse_hours(place)

                if hours:
                    properties["opening_hours"] = hours

                yield GeojsonPointItem(**properties)

            except:
                pass
