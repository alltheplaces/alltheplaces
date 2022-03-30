# -*- coding: utf-8 -*-
import csv
import datetime

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


class HomeGoodsSpider(scrapy.Spider):
    name = "homegoods"
    item_attributes = {"brand": "HomeGoods"}
    allowed_domains = ["tjx.com"]

    chains = {
        "28": "HomeGoods",
    }

    def start_requests(self):
        url = "https://mktsvc.tjx.com/storelocator/GetSearchResults"
        payload = {"chain": "28", "lang": "en", "maxstores": "100", "country": "us"}

        with open(
            "./locations/searchable_points/us_centroids_100mile_radius.csv"
        ) as points:
            reader = csv.DictReader(points)
            for point in reader:
                payload.update(
                    {"geolat": point["latitude"], "geolong": point["longitude"]}
                )

                yield scrapy.http.FormRequest(
                    url=url,
                    method="POST",
                    formdata=payload,
                    headers={
                        "Content-Type": "application/x-www-form-urlencoded",
                        "Accept": "application/json",
                    },
                )

    def parse_hours(self, hours):
        """Mon-Thu: 9am - 9pm, Black Friday: 8am - 10pm, Sat: 9am - 9pm, Sun: 10am - 8pm"""
        opening_hours = OpeningHours()
        hours = hours.replace("Black Friday", "Fri")

        for x in hours.split(","):
            days, hrs = x.split(":", 1)
            try:
                open_time, close_time = hrs.split("-")
            except:
                continue
            open_time = open_time.replace("a", "am").replace("p", "pm")
            close_time = close_time.replace("a", "am").replace("p", "pm")

            if ":" in open_time:
                open_time = datetime.datetime.strptime(
                    open_time.strip(), "%I:%M%p"
                ).strftime("%H:%M")
            else:
                open_time = datetime.datetime.strptime(
                    open_time.strip(), "%I%p"
                ).strftime("%H:%M")

            if ":" in close_time:
                close_time = datetime.datetime.strptime(
                    close_time.strip(), "%I:%M%p"
                ).strftime("%H:%M")
            else:
                close_time = datetime.datetime.strptime(
                    close_time.strip(), "%I%p"
                ).strftime("%H:%M")

            if "-" in days:
                start_day, end_day = days.split("-")
                for day in DAYS[
                    DAYS.index(start_day.strip()) : DAYS.index(end_day.strip()) + 1
                ]:
                    opening_hours.add_range(
                        day[:2], open_time=open_time, close_time=close_time
                    )

            else:
                day = days.strip()[:2]
                opening_hours.add_range(day, open_time=open_time, close_time=close_time)

        return opening_hours.as_opening_hours()

    def parse(self, response):
        data = response.json()

        for store in data["Stores"]:
            properties = {
                "name": store["Name"],
                "ref": store["StoreID"],
                "addr_full": store["Address"].strip(),
                "city": store["City"],
                "state": store["State"],
                "postcode": store["Zip"],
                "country": store["Country"],
                "phone": store["Phone"],
                "lat": float(store["Latitude"]),
                "lon": float(store["Longitude"]),
                "brand": self.chains[store["Chain"]],
            }

            hours = self.parse_hours(store["Hours"])
            if hours:
                properties["opening_hours"] = hours

            yield GeojsonPointItem(**properties)
