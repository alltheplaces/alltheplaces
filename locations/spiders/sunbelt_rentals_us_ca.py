# -*- coding: utf-8 -*-
import json
import re

import scrapy

from locations.items import Feature
from locations.hours import OpeningHours


class SunbeltRentalsUsCaSpider(scrapy.Spider):
    name = "sunbelt_rentals_us_ca"
    item_attributes = {'brand': 'Sunbelt Rentals', "brand_wikidata": "Q102396721"}
    allowed_domains = ['sunbeltrentals.com']

    def start_requests(self):
        yield scrapy.Request(
            "https://api.sunbeltrentals.com/web/api/v1/locations?latitude=39.0171368&longitude=-94.5985613&distance=5000",
            headers={
                "Client_id": "0oa56ipgl8SAfB1kE5d7",
                "Client_secret": "6yNzPOIbav3xJ0XMFRI9cCKjEmqcKXiPVPhQS7eo",
                "Logintoken": "",
                "Request-Id":"12323sunbelt",
                "X-Correlation-Id": "qjElWEoUHtD5oK0uqMbCivbwL632fc23bef67923b234f8c19",
                "Origin": "https://www.sunbeltrentals.com",
                "Referer": "https://www.sunbeltrentals.com/",
                "Sec-Ch-Ua-Platform": "macOS",
                "Authorization": "Bearer",
                "Channel": "WEBAPP",
                "Companyid": 0,
                "Host": "api.sunbeltrentals.com"
            }, method="GET",
            callback=self.parse,
        )

    def parse_hours(self, hours):
        opening_hours = OpeningHours()

        for hour in hours:
            day = hour["day"][:2]
            if hour["hours"]=="Closed":
                pass
            else:
                try:
                    o = hour["open"].split("T")
                    open = o[1]
                    c = hour["close"].split("T")
                    close = c[1]
                    opening_hours.add_range(
                        day=day,
                        open_time=open,
                        close_time=close,
                        time_format="%H:%M:%S")
                except:
                    o = hour["hours"].split(" - ")
                    open = o[0]
                    close = o[1]
                    opening_hours.add_range(
                        day=day,
                        open_time=open,
                        close_time=close,
                        time_format="%I:%M %p")

        return opening_hours.as_opening_hours()

    def parse(self, response):
        data = response.json()

        for store in data["data"]["pcList"]:
            properties = {
                'ref': store["pc"],
                'name': store["name"],
                'street_address': store["street"],
                'city': store["city"],
                'state': store["state"],
                'postcode': store["zip"],
                'lat': store["latitude"],
                'lon': store["longitude"],
                'phone': store["phone"],
            }

            hours = self.parse_hours(store["operatingHours"])
            if hours:
                properties["opening_hours"] = hours

            yield Feature(**properties)

