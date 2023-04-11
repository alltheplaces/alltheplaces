import json

import scrapy

from locations.hours import DAYS_EN, DAYS_FULL, OpeningHours
from locations.items import Feature


class EccoSpider(scrapy.Spider):
    name = "ecco"
    item_attributes = {"brand": "Ecco", "brand_wikidata": "Q1280255"}
    start_urls = [
        "https://se.ecco.com/api/store/search?latitudeMin=-90&longitudeMin=-180&latitudeMax=90&longitudeMax=180"
    ]
    custom_settings = {"ROBOTSTXT_OBEY": False}
    download_delay = 0.1

    def parse(self, response):
        stores = json.loads(response.text)
        for store in stores:
            if "ecco" in store["n"].lower():
                yield scrapy.Request(
                    url="https://se.ecco.com/api/store/finder/" + store["i"], callback=self.parse_store
                )

    def parse_store(self, response):
        store = json.loads(response.text)
        item = Feature()
        item["ref"] = store["StoreId"]
        item["name"] = store["Name"]
        item["street_address"] = store["Street"]
        item["housenumber"] = store["HouseNr"]
        item["city"] = store["City"]
        item["postcode"] = store["PostalCode"]
        item["phone"] = store["Phone"]
        item["country"] = store["CountryCode"]
        item["email"] = store["Email"]
        item["lat"] = store["Latitude"]
        item["lon"] = store["Longitude"]
        oh = OpeningHours()
        for day in DAYS_FULL:
            ranges_string = day + " " + store[day + "Open"] + "-" + store[day + "Close"]
            oh.add_ranges_from_string(ranges_string=ranges_string, days=DAYS_EN, delimiters=["-"])

        item["opening_hours"] = oh.as_opening_hours()
        yield item
