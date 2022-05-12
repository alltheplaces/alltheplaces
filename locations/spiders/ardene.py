# -*- coding: utf-8 -*-
import scrapy
from locations.hours import OpeningHours
from locations.items import GeojsonPointItem

DAYS_NAME = {
    "Monday": "Mo",
    "Tuesday": "Tu",
    "Wednesday": "We",
    "Thursday": "Th",
    "Friday": "Fr",
    "Saturday": "Sa",
    "Sunday": "Su",
}


class ArdeneSpider(scrapy.Spider):
    name = "ardene"
    item_attributes = {"brand": "Ardene", "brand_wikidata": "Q2860764"}
    allowed_domains = ["www.ardene.com"]
    start_urls = ("https://www.ardene.com/us/en/stores/",)

    def parse(self, response):
        url = "https://www.ardene.com/on/demandware.store/Sites-ardene-Site/en_US/Stores-GetStoresUpdate"

        formdata = {
            "distanceUnit": "mi",
            "maxDistance": "1000000",
            "lat": "56.1304",
            "lng": "-102.34680000000003",
            "maxStores": "1000000",
        }

        yield scrapy.http.FormRequest(
            url,
            self.parse_store,
            method="POST",
            formdata=formdata,
        )

    def parse_hours(self, hours):
        day_hour = hours.split("\n")

        opening_hours = OpeningHours()

        for dh in day_hour:
            try:
                day = DAYS_NAME[dh.split(" ")[0]]
                hr = dh.split(" ")[1]
                open_time, close_time = hr.split("-")
                opening_hours.add_range(
                    day=day,
                    open_time=open_time,
                    close_time=close_time,
                    time_format="%H:%M",
                )
            except:
                continue

        return opening_hours.as_opening_hours()

    def parse_store(self, response):
        store_data = response.json()

        for store in store_data:

            properties = {
                "ref": store["name"],
                "addr_full": " ".join(
                    [store["address1"], store.get("address2", "") or ""]
                ).strip(),
                "city": store["city"],
                "state": store["stateCode"],
                "postcode": store["postalCode"],
                "lat": store["latitude"],
                "lon": store["longitude"],
                "phone": store["phone"],
                "name": store["name"],
                "country": store["countryCode"],
            }

            hours = self.parse_hours(store["storeHours"])
            if hours:
                properties["opening_hours"] = hours

            yield GeojsonPointItem(**properties)
