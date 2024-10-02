import scrapy

from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature


class EccoSpider(scrapy.Spider):
    name = "ecco"
    item_attributes = {"brand": "Ecco", "brand_wikidata": "Q1280255"}
    start_urls = [
        "https://se.ecco.com/api/store/search?latitudeMin=-90&longitudeMin=-180&latitudeMax=90&longitudeMax=180"
    ]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response):
        for store in response.json():
            if store["t"] in [
                # 0,  # PARTNER # Just sell the stock?
                1,  # ECCO
                2,  # Outlet
                4,  # Large store?
            ]:
                yield scrapy.Request(
                    url="https://se.ecco.com/api/store/finder/" + store["i"], callback=self.parse_store
                )

    def parse_store(self, response):
        store = response.json()
        if store["StoreType"] == "FullPrice":
            return  # Online/virtual store
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
        item["extras"]["store_type"] = store["StoreType"]
        oh = OpeningHours()
        for day in DAYS_FULL:
            oh.add_range(day, store[f"{day}Open"], store[f"{day}Close"], time_format="%H:%M:%S")

        item["opening_hours"] = oh
        yield item
