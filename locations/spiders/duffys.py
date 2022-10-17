# -*- coding: utf-8 -*-
import scrapy

from locations.hours import DAYS_EN
from locations.items import GeojsonPointItem


class Duffys(scrapy.Spider):

    name = "duffys"
    item_attributes = {"brand": "Duffys"}
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def start_requests(self):
        url = "https://api.duffysmvp.com/api/app/nearByLocations"
        yield scrapy.Request(
            url,
            method="POST",
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            body='{"latitude":"26.6289791","longitude":"-80.0724384"}',
            callback=self.parse,
        )

    def parse(self, response):
        results = response.json()

        for store in results:
            address_results = store.get("address")
            oh = (
                store.get("hoursOfOperation")
                .replace(":", "")
                .replace(",", ";")
                .replace(" - ", "-")
                .replace("Daily", "Mo-Su")
                .replace("am", ":00")
                .replace("pm", ":00")
                .lstrip(" ")
            )
            for k, v in DAYS_EN.items():
                oh = oh.replace(k, v)

            properties = {
                "ref": store.get("code"),
                "name": store.get("name"),
                "street_address": address_results.get("address1"),
                "city": address_results.get("city"),
                "country": address_results.get("country"),
                "phone": address_results.get("phone"),
                "state": address_results.get("stateProvince"),
                "postcode": address_results.get("postalCode"),
                "opening_hours": oh,
                "lat": store.get("latitude"),
                "lon": store.get("longitude"),
            }

            yield GeojsonPointItem(**properties)
