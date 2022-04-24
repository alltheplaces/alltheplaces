# -*- coding: utf-8 -*-
import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class CostaCoffeeIESpider(scrapy.Spider):
    name = "costacoffee_ie"
    item_attributes = {"brand": "Costa Coffee"}
    allowed_domains = ["costaireland.ie"]
    # May need to do pagination at some point
    start_urls = ["https://www.costaireland.ie/api/cf/?content_type=storeV2&limit=500"]

    def parse(self, response):
        jsonresponse = response.json()
        for store_data in jsonresponse["items"]:
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
                properties["extras"]["store_type"] = "store"
            elif label.startswith("EXPRESS"):
                properties["extras"]["store_type"] = "express"
            else:
                properties["extras"]["operator"] = data["cmsLabel"]

            opening_hours = OpeningHours()
            for day in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]:
                if "open" + day in data:
                    opening_hours.add_range(
                        day[0:2],
                        data["open" + day],
                        data["close" + day],
                    )
            properties["opening_hours"] = opening_hours.as_opening_hours()

            yield GeojsonPointItem(**properties)
