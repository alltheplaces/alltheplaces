# -*- coding: utf-8 -*-
import scrapy
import json

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours

DAY_MAPPING = {
    "2": "Mo",
    "3": "Tu",
    "4": "We",
    "5": "Th",
    "6": "Fr",
    "7": "Sa",
    "1": "Su",
}


class BostonPizzaSpider(scrapy.Spider):
    name = "bostonpizza"
    item_attributes = {"brand": "Boston Pizza"}
    allowed_domains = ["www.bostonpizza.com"]
    start_urls = ("https://bostonpizza.com/en/locations.html",)

    def start_requests(self):
        template = "https://bostonpizza.com/content/bostonpizza/jcr:content/leftnavigation.en.getAllStores.json"

        headers = {
            "Accept": "application/json",
        }

        yield scrapy.http.FormRequest(
            url=template, method="GET", headers=headers, callback=self.parse
        )

    def parse(self, response):
        jsonresponse = response.json()
        for stores in jsonresponse:
            store = json.dumps(stores)
            store_data = json.loads(store)

            properties = {
                "ref": store_data["storeId"],
                "name": store_data["restaurantName"],
                "addr_full": store_data["address1"],
                "city": store_data["city"],
                "state": store_data["province"],
                "postcode": store_data["postalCode"],
                "country": store_data["country"],
                "lon": float(store_data["longitude"]),
                "lat": float(store_data["latitude"]),
            }

            hours = store_data["storeHours"]["DayList"]

            if hours:
                properties["opening_hours"] = self.process_hours(hours)

            yield GeojsonPointItem(**properties)

    def process_hours(self, hours):
        opening_hours = OpeningHours()

        for hour in hours:
            day = hour["DayOfWeek"]
            open_time = hour["TimeOpen"]
            close_time = hour["TimeClose"]

            opening_hours.add_range(
                day=DAY_MAPPING[day],
                open_time=open_time,
                close_time=close_time,
                time_format="%H:%M:%S",
            )
        return opening_hours.as_opening_hours()
