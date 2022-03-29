# -*- coding: utf-8 -*-
import json
import re

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class NationalTireBatterySpider(scrapy.Spider):
    name = "national_tire_battery"
    item_attributes = {"brand": "National Tire & Battery"}
    allowed_domains = ["ntb.com"]
    start_urls = [
        "https://www.ntb.com/rest/model/com/tbc/store/StoreLocatorService/getAllActiveStores"
    ]

    def parse_hours(self, hours):
        opening_hours = OpeningHours()
        for hour in hours:
            if hour["openingHour"] == "CLOSED":
                continue
            opening_hours.add_range(
                day=hour["day"][:2],
                open_time=hour["openingHour"],
                close_time=hour["closingHour"],
                time_format="%I:%M %p",
            )
        return opening_hours.as_opening_hours()

    def parse_store(self, response):
        data = response.json()

        store = data["output"]["store"]
        properties = {
            "ref": store["storeNumber"],
            "addr_full": store["address"]["address1"],
            "city": store["address"]["city"],
            "state": store["address"]["state"],
            "postcode": store["address"]["zipcode"],
            "phone": store["phoneNumbers"][0],
            "website": store["brand"]["viewStoreURL"] + store["storeNumber"],
            "lat": float(store["mapCenter"]["latitude"]),
            "lon": float(store["mapCenter"]["longitude"]),
        }

        hours = self.parse_hours(store["workingHours"])
        if hours:
            properties["opening_hours"] = hours

        yield GeojsonPointItem(**properties)

    def parse(self, response):
        data = response.json()
        for store in data["output"]["storeDetailList"]:
            store_number = re.search(r"(\d+)\s-\s.+", store).groups()[0]
            yield scrapy.Request(
                "https://www.ntb.com/rest/model/com/tbc/store/StoreLocatorService/getStoreDetailsByID",
                method="POST",
                body=json.dumps({"storeID": store_number}),
                headers={"Content-Type": "application/json"},
                callback=self.parse_store,
            )
