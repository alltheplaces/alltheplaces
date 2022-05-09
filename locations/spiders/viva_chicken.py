# -*- coding: utf-8 -*-
import json
from urllib.parse import urlencode

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours

BASE_URL = "https://www.vivachicken.com/wp-admin/admin-ajax.php?"
DAY_MAPPING = {
    "sun": "Su",
    "mon": "Mo",
    "tue": "Tu",
    "wed": "We",
    "thu": "Th",
    "fri": "Fr",
    "sat": "Sa",
}


class VivaChickenSpider(scrapy.Spider):
    name = "viva_chicken"
    item_attributes = {"brand": "Viva Chicken"}
    allowed_domains = ["www.vivachicken.com"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def start_requests(self):
        params = {
            "action": "asl_load_stores",
            "nonce": "c1b90b7b16",
            "load_all": 1,
            "layout": 1,
        }

        yield scrapy.http.Request(
            url=BASE_URL + urlencode(params),
            callback=self.parse,
            method="GET",
        )

    def parse_hours(self, hours):
        opening_hours = OpeningHours()
        store_hours = json.loads(hours)

        for k, v in DAY_MAPPING.items():
            open_hours = store_hours.get(k)
            if not open_hours:
                continue
            open_time, close_time = open_hours[0].split(" - ")

            opening_hours.add_range(
                day=v,
                open_time=open_time,
                close_time=close_time,
                time_format="%I:%M %p",
            )

        return opening_hours.as_opening_hours()

    def parse(self, response):
        locations = json.loads(response.text)

        for location in locations:
            properties = {
                "ref": location["id"],
                "name": location["title"],
                "addr_full": location["street"],
                "city": location["city"],
                "state": location["state"],
                "postcode": location["postal_code"],
                "country": location["country"],
                "lat": location["lat"],
                "lon": location["lng"],
                "phone": location["phone"],
                "website": location["website"],
            }

            hours = location.get("open_hours")
            if hours:
                properties["opening_hours"] = self.parse_hours(hours)

            yield GeojsonPointItem(**properties)
