# -*- coding: utf-8 -*-
import json
import scrapy
from locations.items import GeojsonPointItem
from locations.hours import OpeningHours

weekdays = [
    "sunday",
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
]
day_mapping = {
    "sunday": "Su",
    "monday": "Mo",
    "tuesday": "Tu",
    "wednesday": "We",
    "thursday": "Th",
    "friday": "Fr",
    "saturday": "Sa",
}


def convert_24hour(time):
    """
    Takes 12 hour time as a string and converts it to 24 hour time.
    """
    # Check if 12:00 AM
    if time[-2:] == "AM" and time[:2] == "12":
        return "00" + time[2:-2]

    # Remove AM
    elif time[-2:] == "AM":
        return time[:-2]

    # Check if 12:00 PM
    elif time[-2:] == "PM" and time[:2] == "12":
        return time[:-2]

    else:
        # add 12 hours and remove PM
        return str(int(time[:2]) + 12) + time[2:-2]


class ChristmasTreeShopsSpider(scrapy.Spider):
    name = "christmas_tree_shops"
    item_attributes = {"brand": "Christmas Tree Shops"}
    allowed_domains = ["www.christmastreeshops.com"]
    start_urls = [
        "https://www.christmastreeshops.com/store-locator",
    ]

    def parse(self, request):
        url = "https://www.christmastreeshops.com/api/commerce/storefront/locationUsageTypes/SP/locations/"
        yield scrapy.Request(url, self.parse_store)

    def parse_store(self, response):
        json_data = json.loads(response.text)
        stores = json_data["items"]
        for store_data in stores:
            properties = {
                "name": store_data["name"],
                "ref": store_data["code"],
                "addr_full": store_data["address"]["address1"],
                "city": store_data["address"]["cityOrTown"],
                "state": store_data["address"]["stateOrProvince"],
                "postcode": store_data["address"]["postalOrZipCode"],
                "country": store_data["address"]["countryCode"],
                "phone": store_data.get("phone"),
                "lat": float(store_data["geo"]["lat"]),
                "lon": float(store_data["geo"]["lng"]),
            }

            hours = self.parse_hours(store_data.get("regularHours"))
            if hours:
                properties["opening_hours"] = hours

            yield GeojsonPointItem(**properties)

    def parse_hours(self, open_hours):
        opening_hours = OpeningHours()

        for weekday in weekdays:
            day = day_mapping[weekday]
            day_hours = open_hours.get(weekday).get("label")

            # Check if store is closed that day
            if day_hours in ("x", ""):
                continue

            open_time = convert_24hour(day_hours.split("-")[0])
            close_time = convert_24hour(day_hours.split("-")[1])
            opening_hours.add_range(day=day, open_time=open_time, close_time=close_time)

        return opening_hours.as_opening_hours()
