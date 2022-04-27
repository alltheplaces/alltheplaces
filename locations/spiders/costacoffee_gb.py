# -*- coding: utf-8 -*-
import csv
import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class CostaCoffeeGBSpider(scrapy.Spider):
    name = "costacoffee_gb"
    item_attributes = {"brand": "Costa Coffee", "brand_wikidata": "Q608845"}
    allowed_domains = ["www.costa.co.uk"]
    download_delay = 1

    def start_requests(self):
        template = "https://www.costa.co.uk/api/locations/stores?latitude={lat}&longitude={lon}&maxrec=600"
        # TODO: Can't figure out how to return more than 5 miles

        with open(
            "./locations/searchable_points/eu_centroids_20km_radius_country.csv"
        ) as points:
            reader = csv.DictReader(points)
            for point in reader:
                if point["country"] == "UK":
                    yield scrapy.http.Request(
                        url=template.format(
                            lat=point["latitude"], lon=point["longitude"]
                        ),
                        callback=self.parse,
                    )

    def parse(self, response):
        jsonresponse = response.json()
        for store_data in jsonresponse["stores"]:
            addr_full = ", ".join(
                filter(
                    None,
                    (
                        store_data["storeAddress"]["addressLine1"],
                        store_data["storeAddress"]["addressLine2"],
                        store_data["storeAddress"]["addressLine3"],
                        store_data["storeAddress"]["city"],
                        store_data["storeAddress"]["postCode"],
                        "United Kingdom",
                    ),
                ),
            )

            opening_hours = OpeningHours()
            for day in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]:
                if store_data["storeOperatingHours"]["open" + day] != "":
                    opening_hours.add_range(
                        day[0:2],
                        store_data["storeOperatingHours"]["open" + day],
                        store_data["storeOperatingHours"]["close" + day],
                    )

            properties = {
                "ref": store_data["storeNo8Digit"],
                "name": store_data["storeNameExternal"],
                "addr_full": addr_full.strip(),
                "street_address": store_data["storeAddress"]["addressLine1"],
                "city": store_data["storeAddress"]["city"],
                "postcode": store_data["storeAddress"]["postCode"],
                "country": store_data["storeAddress"]["country"],
                "lat": float(store_data["latitude"]),
                "lon": float(store_data["longitude"]),
                "phone": store_data["telephone"],
                "opening_hours": opening_hours.as_opening_hours(),
                "extras": {
                    "email": store_data["email"],
                    "store_type": store_data["storeType"],
                    "storeBusinessModel": store_data["storeBusinessModel"],
                },
            }

            for storeFacility in store_data["storeFacilities"]:
                if storeFacility["name"] == "Wifi":
                    if storeFacility["active"]:
                        properties["extras"]["internet_access"] = "wlan"
                    else:
                        properties["extras"]["internet_access"] = "no"
                elif storeFacility["name"] == "Disabled WC":
                    if storeFacility["active"]:
                        properties["extras"]["toilets"] = "yes"
                        properties["extras"]["toilets:wheelchair"] = "yes"
                    else:
                        properties["extras"]["toilets:wheelchair"] = "no"
                elif storeFacility["name"] == "Baby Changing":
                    if storeFacility["active"]:
                        properties["extras"]["changing_table"] = "yes"
                    else:
                        properties["extras"]["changing_table"] = "no"
                elif storeFacility["name"] == "Disabled Access":
                    if storeFacility["active"]:
                        properties["extras"]["wheelchair"] = "yes"
                    else:
                        properties["extras"]["wheelchair"] = "no"
                elif storeFacility["name"] == "Drive Thru":
                    if storeFacility["active"]:
                        properties["extras"]["drive_through"] = "yes"
                    else:
                        properties["extras"]["drive_through"] = "no"
                elif storeFacility["name"] == "Delivery":
                    if storeFacility["active"]:
                        properties["extras"]["delivery"] = "yes"
                    else:
                        properties["extras"]["delivery"] = "no"

            if store_data["storeStatus"] == "TRADING":
                yield GeojsonPointItem(**properties)
