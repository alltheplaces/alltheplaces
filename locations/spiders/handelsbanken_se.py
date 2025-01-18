import json

import scrapy

from locations.categories import Categories, apply_category, apply_yes_no
from locations.hours import DAYS, OpeningHours
from locations.items import Feature


class HandelsbankenSESpider(scrapy.Spider):
    name = "handelsbanken_se"
    item_attributes = {"brand": "Handelsbanken", "brand_wikidata": "Q1421630"}
    start_urls = [
        "https://locator.maptoweb.dk/handelsbanken.com/locator/points/where/CountryCode/eqi/se?callback=jQuery1820675693055071215_1676888222517&_=1676888222528"
    ]

    def parse(self, response, **kwargs):
        stores_raw = response.text
        stores = json.loads(stores_raw.replace("jQuery1820675693055071215_1676888222517(", "").rstrip(");"))

        for store in stores.get("results"):
            oh = OpeningHours()
            location_type = None
            for options in store.get("options"):
                if options.get("name") == "LocationType":
                    location_type = options.get("value")
                if options.get("name") != "OpenHoursSpan":
                    continue
                oh_json = json.loads(options.get("value"))
                for day in oh_json:
                    oh.add_range(DAYS[int(day.get("Weekday"))], day.get("Open"), day.get("Close"))
            if website := store.get("url") and website and website.startswith("www."):
                website = website.replace("www.", "https://www.")
            properties = {
                "ref": str(store.get("id")),
                "name": store.get("name"),
                "housenumber": store.get("houseNumber"),
                "postcode": store.get("zipCode"),
                "city": store.get("cityName"),
                "country": store.get("countryCode"),
                "street_address": store.get("streetName"),
                "phone": store.get("phone"),
                "email": store.get("email"),
                "website": website,
                "lat": store.get("location").get("lat"),
                "lon": store.get("location").get("lng"),
                "opening_hours": oh,
            }
            if location_type in ["ATM", "CRS"]:
                apply_category(Categories.ATM, properties)
                if location_type == "CRS":
                    apply_yes_no("cash_out", properties, True)
            elif location_type == "Branch":
                apply_category(Categories.BANK, properties)
            yield Feature(**properties)
