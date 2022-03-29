# -*- coding: utf-8 -*-
import re

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class OlliesBargainOutletSpider(scrapy.Spider):
    name = "ollies_bargain_outlet"
    allowed_domains = ["ollies.us"]

    def start_requests(self):
        url = "https://www.ollies.us/admin/locations/ajax.aspx"

        headers = {
            "origin": "https://www.ollies.us",
            "Referer": "https://www.ollies.us/locations/",
        }

        for n in range(1, 85):
            formdata = {
                "Page": str(n),
                "PageSize": "5",
                "StartIndex": "0",
                "EndIndex": "5",
                "Longitude": "-97.708694",
                "Latitude": "30.377566",
                "City": "",
                "State": "",
                "F": "GetNearestLocations",
                "RangeInMiles": "5000",
            }

            yield scrapy.http.FormRequest(
                url, self.parse, method="POST", headers=headers, formdata=formdata
            )

    def parse_hours(self, hours):
        opening_hours = OpeningHours()
        other_days = ["Mo", "Tu", "We", "Th", "Fr", "Sa"]

        hours_list = hours.split("<br />")
        hours_list.pop()

        if "Coming soon!" not in hours_list:
            for h in hours_list:
                d, time = h.split(": ")
                start_time, end_time = time.split("-")

                if d == "Sunday":
                    day = "Su"
                    opening_hours.add_range(
                        day=day,
                        open_time=start_time,
                        close_time=end_time,
                        time_format="%H%p",
                    )

                if d == "Monday-Saturday":
                    for day in other_days:
                        opening_hours.add_range(
                            day=day,
                            open_time=start_time,
                            close_time=end_time,
                            time_format="%H%p",
                        )

        return opening_hours.as_opening_hours()

    def parse(self, response):
        data = response.json()

        for store in data["Locations"]:
            properties = {
                "ref": store["StoreCode"],
                "name": store["Name"],
                "addr_full": store["Address1"],
                "city": store["City"],
                "state": store["State"],
                "postcode": store["Zip"],
                "country": "US",
                "lat": store["Latitude"],
                "lon": store["Longitude"],
                "phone": store["Phone"],
                "website": "https://www.ollies.us" + store["CustomUrl"],
            }

            try:
                hours = self.parse_hours(store["OpenHours"])

                if hours:
                    properties["opening_hours"] = hours
            except:
                pass

            yield GeojsonPointItem(**properties)
