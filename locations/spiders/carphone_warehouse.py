import re
import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours

DAYS = {
    "monday": "Mo",
    "tuesday": "Tu",
    "wednesday": "We",
    "friday": "Fr",
    "thursday": "Th",
    "saturday": "Sa",
    "sunday": "Su",
}


class CarphoneWarehouseSpider(scrapy.Spider):
    name = "carphonewarehouse"
    item_attributes = {"brand": "Carphone Warehouse", "brand_wikidata": "Q118046"}
    allowed_domains = ["www.carphonewarehouse.com"]
    custom_settings = {"ROBOTSTXT_OBEY": False}
    start_urls = [
        "https://www.carphonewarehouse.com/services/storedata?filter=&count=1000000&lat=54.2526491&lng=-2.0411242"
    ]

    def store_hours(self, store_hours):
        oh = OpeningHours()
        for key1, value1 in DAYS.items():
            if key1 in store_hours:
                open_time, close_time = store_hours[key1].split(" - ")
                oh.add_range(value1, open_time, close_time)
        return oh.as_opening_hours()

    def parse(self, response):
        data = response.json()
        for key, value in data.items():
            if "AddressLine" in value:
                addr_full = value["AddressLine"].split(",")
                address = ", ".join(addr_full[: len(addr_full) - 1])
                city = addr_full[len(addr_full) - 1]
            else:
                address = ""
                city = ""
            if "postcode" in value:
                postcode = value["postcode"]
            else:
                postcode = ""
            properties = {
                "ref": key,
                "name": value["branch_name"],
                "street_address": address,
                "city": city,
                "postcode": postcode,
                "lat": value["Latitude"],
                "lon": value["Longitude"],
                "phone": value.get("telephone"),
                "website": "https://www.carphonewarehouse.com/store-locator/"
                + value["pageName"]
                + ".html",
            }

            opening_hours = self.store_hours(value)
            if opening_hours:
                properties["opening_hours"] = opening_hours

            yield GeojsonPointItem(**properties)
