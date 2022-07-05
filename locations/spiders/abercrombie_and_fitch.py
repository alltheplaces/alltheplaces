# -*- coding: utf-8 -*-
import re

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class AbercrombieAndFitchSpider(scrapy.Spider):
    name = "abercrombie_and_fitch"
    item_attributes = {"brand": "Abercrombie and Fitch"}
    allowed_domains = ["abercrombie.com"]
    # Website is blocking scrapers so I had to change the User Agent to get around this
    headers = {
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36",
    }
    custom_settings = {
        "ROBOTSTXT_OBEY": False,
    }

    def start_requests(self):
        countries = [
            "US",
            "CA",
            "BE",
            "FR",
            "DE",
            "HK",
            "IE",
            "IT",
            "JP",
            "KW",
            "CN",
            "MX",
            "NL",
            "QA",
            "SA",
            "SG",
            "ES",
            "AE",
            "GB",
        ]

        for country in countries:
            yield scrapy.Request(
                url=f"https://www.abercrombie.com/api/ecomm/a-ca/storelocator/search?country={country}",
                method="GET",
                callback=self.parse,
                headers=self.headers,
            )

    def parse(self, response):
        data = response.json()

        for row in data["physicalStores"]:
            for brand in row["physicalStoreAttribute"]:
                if brand["name"] == "Brand":
                    brandValue = brand["value"]
            properties = {
                "ref": row["storeNumber"],
                "name": row["name"],
                "country": row["country"],
                "state": row["stateOrProvinceName"],
                "city": row["city"],
                "lat": row["latitude"],
                "lon": row["longitude"],
                "phone": row["telephone"],
                "addr_full": row["addressLine"][0],
                "postcode": row["postalCode"],
                "brand": brandValue,
            }

            yield GeojsonPointItem(**properties)
