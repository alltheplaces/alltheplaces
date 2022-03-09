# -*- coding: utf-8 -*-
import json
import re

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours

DAY_MAPPING = {
    "Mon": "Mo",
    "Tue": "Tu",
    "Wed": "We",
    "Thu": "Th",
    "Fri": "Fr",
    "Sat": "Sa",
    "Sun": "Su",
}


class ScootersCoffeeSpider(scrapy.Spider):
    name = "scooters_coffee"
    item_attributes = {"brand": "Scooter's Coffee"}
    allowed_domains = ["code.metalocator.com"]
    download_delay = 0.5

    def start_requests(self):
        n = 327
        for store_id in range(1, n + 1):
            url = f"https://code.metalocator.com/index.php?option=com_locator&view=location&tmpl=component&task=load&framed=1&sample_data=undefined&format=json&Itemid=12991&templ[]=item_address_template&lang=&_opt_out=&_urlparams=&distance=NaN&id={store_id}"

            yield scrapy.Request(url=url, callback=self.parse)

    def parse_hours(self, hours):
        opening_hours = OpeningHours()

        weekdays = re.findall(r"{(.*?)}", hours)
        for weekday in weekdays:
            day, open_close = weekday.split("|")
            if open_close == "C":
                continue
            else:
                open_close = open_close.replace(" ", "")
                open_time, close_time = open_close.split("-")
                opening_hours.add_range(
                    day=DAY_MAPPING[day],
                    open_time=open_time,
                    close_time=close_time,
                    time_format="%I:%M%p",
                )

        return opening_hours.as_opening_hours()

    def parse(self, response):
        store_data = json.loads(response.text)[0]
        name = store_data["name"]
        if "*permanently closed" in name.lower():
            pass
        else:  # Gather the store details

            properties = {
                "ref": store_data["id"],
                "name": store_data["name"].strip(" *COMING SOON"),
                "addr_full": store_data["address"],
                "city": store_data["city"],
                "state": store_data["state"],
                "postcode": store_data["postalcode"],
                "country": store_data["country"],
                "lat": store_data["lat"],
                "lon": store_data["lng"],
                "phone": store_data["phone"],
                "website": response.url,
            }

            hours = store_data.get("hours", "")
            if hours and hours != "{Sun|C}{Mon|C}{Tue|C}{Wed|C}{Thu|C}{Fri|C}{Sat|C}":
                store_hours = self.parse_hours(hours)
                properties["opening_hours"] = store_hours

            yield GeojsonPointItem(**properties)
