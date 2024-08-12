import re

import scrapy

from locations.items import Feature


class SimonmedSpider(scrapy.Spider):
    name = "simonmed"
    item_attributes = {"brand": "SimonMed"}
    allowed_domains = ["www.simonmed.com"]
    start_urls = ("https://www.simonmed.com/locations/getLocations",)

    def parse_times(self, hour):
        if re.search("PM$", hour):
            hour = re.sub("PM", "", hour).strip()
            hour_min = hour.split(":")
            if int(hour_min[0]) < 12:
                hour_min[0] = str(12 + int(hour_min[0]))
            return ":".join(hour_min)

        if re.search("AM$", hour):
            hour = re.sub("AM", "", hour).strip()
            hour_min = hour.split(":")
            if len(hour_min[0]) < 2:
                hour_min[0] = hour_min[0].zfill(2)
            else:
                hour_min[0] = str(12 + int(hour_min[0]))
            return ":".join(hour_min)

    def parse(self, response):
        data = response.json()
        for store in data:
            opening_hours = []

            for day_hour in store["Days"]:
                opening_hours.append(
                    day_hour["Day"][:2]
                    + " "
                    + self.parse_times(day_hour["Open"])
                    + "-"
                    + self.parse_times(day_hour["Close"])
                )

            properties = {
                "addr_full": store["Street1"] + " " + store["Street2"],
                "phone": store["PhoneNumber"],
                "city": store["City"],
                "state": store["State"],
                "postcode": store["ZipCode"],
                "name": store["Name"],
                "ref": store["id"],
                "website": "https://www.simonmed.com/locations",
                "lat": store["Latitude"],
                "lon": store["Longitude"],
                "opening_hours": "; ".join(opening_hours),
            }

            yield Feature(**properties)

    def start_requests(self):
        headers = {
            "Accept-Language": "en-US,en;q=0.8,ru;q=0.6",
            "Origin": "www.simonmed.com",
            "Accept-Encoding": "gzip, deflate",
            "Accept": "*/*",
            "Referer": "https://www.simonmed.com/locations",
            "Connection": "keep-alive",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36",
        }
        form_data = {
            "location": "85251",
            "miles": "1000000",
            "location_lat": "33.4986286",
            "location_lng": "-111.9224398",
        }

        yield scrapy.http.FormRequest(
            self.start_urls[0],
            method="POST",
            formdata=form_data,
            headers=headers,
        )
