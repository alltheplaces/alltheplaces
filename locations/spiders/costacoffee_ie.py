# -*- coding: utf-8 -*-
import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours, DAYS_FULL


class CostaCoffeeIESpider(scrapy.Spider):
    name = "costacoffee_ie"
    item_attributes = {"brand": "Costa Coffee", "brand_wikidata": "Q608845"}
    allowed_domains = ["costaireland.ie"]
    # May need to do pagination at some point
    start_urls = [
        "https://www.costaireland.ie/api/cf/?content_type=storeLocatorStore&limit=1000"
    ]

    def parse(self, response):
        for store_data in response.json()["items"]:
            data = store_data["fields"]

            properties = {
                "ref": store_data["sys"]["id"],
                "name": data["storeName"],
                "addr_full": data["storeAddress"],
                "country": "IE",
                "lat": float(data["location"]["lat"]),
                "lon": float(data["location"]["lon"]),
                "extras": {},
            }

            label = data["cmsLabel"]
            if label.startswith("STORE"):
                properties["extras"]["amenity"] = "cafe"
                properties["extras"]["cuisine"] = "coffee_shop"
            elif label.startswith("EXPRESS"):
                properties["brand"] = "Costa Express"
                properties["extras"]["amenity"] = "vending_machine"
                properties["extras"]["vending"] = "coffee"
            else:
                properties["extras"]["operator"] = label

            opening_hours = OpeningHours()
            for day in DAYS_FULL:
                if day.lower() + "Opening" in data:
                    opening_hours.add_range(
                        day[0:2],
                        data[day.lower() + "Opening"],
                        data[day.lower() + "Closing"],
                    )
            properties["opening_hours"] = opening_hours.as_opening_hours()

            yield GeojsonPointItem(**properties)
