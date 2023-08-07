import json

import scrapy

from locations.items import Feature

HEADERS = {"Content-Type": "application/json"}


class LovesSpider(scrapy.Spider):
    name = "loves"
    item_attributes = {
        "brand": "Love's Travel Stops & Country Stores",
        "brand_wikidata": "Q1872496",
    }
    allowed_domains = ["www.loves.com"]
    download_delay = 0.2

    def start_requests(self):
        payload = json.dumps(
            {
                "StoreTypes": [],
                "Amenities": [],
                "Restaurants": [],
                "FoodConcepts": [],
                "State": "All",
                "City": "All",
                "Highway": "All",
            }
        )
        yield scrapy.Request(
            "https://www.loves.com/api/sitecore/StoreSearch/SearchStores",
            method="POST",
            body=payload,
            headers=HEADERS,
        )

    def parse(self, response):
        stores = response.json()
        for store in stores[0]["Points"]:
            yield Feature(
                name=store["Name"],
                ref=store["SiteId"],
                street_address=store["Address1"],
                city=store["City"],
                state=store["State"],
                postcode=store["Zip"],
                phone=store["PhoneNumber"],
                lat=float(store["Latitude"]),
                lon=float(store["Longitude"]),
            )
