# -*- coding: utf-8 -*-
import scrapy
import json
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


class WhiteHouseBlackMarketSpider(scrapy.Spider):
    download_delay = 0.2
    name = "stagestore"
    item_attributes = {"brand": "Stage"}
    allowed_domains = ["stage.com"]
    start_urls = ("https://stores.stage.com/",)

    def start_requests(self):
        template = "https://api.sweetiq.com/store-locator/public/locations/59e11ed8bad8974a65de9628?search&searchFields%5B0%5D=name"

        headers = {
            "Accept": "application/json",
        }

        yield scrapy.http.FormRequest(
            url=template, method="GET", headers=headers, callback=self.parse
        )

    def parse(self, response):
        jsonresponse = response.json()
        for stores in jsonresponse["records"]:
            store = json.dumps(stores)
            store_data = json.loads(store)
            properties = {
                "name": store_data["slug"],
                "ref": store_data["branch"],
                "addr_full": store_data["address"],
                "city": store_data["city"],
                "state": store_data["province"],
                "postcode": store_data["postalCode"],
                "country": store_data["country"],
                "phone": store_data["phone"],
                "website": store_data["website"],
                "lat": float(store_data["geo"][1]),
                "lon": float(store_data["geo"][0]),
            }

            hours = store_data["hoursOfOperation"]

            if hours:
                properties["opening_hours"] = self.process_hours(hours)

            yield GeojsonPointItem(**properties)

    def process_hours(self, hours):
        opening_hours = OpeningHours()

        for hour in hours:
            if len(hours.get(hour)) == 0:
                continue
            else:
                day = hour
                open_time = hours.get(hour)[0][0]
                close_time = hours.get(hour)[0][1]

                opening_hours.add_range(
                    day=DAY_MAPPING[day],
                    open_time=open_time,
                    close_time=close_time,
                    time_format="%H:%M",
                )
        return opening_hours.as_opening_hours()
