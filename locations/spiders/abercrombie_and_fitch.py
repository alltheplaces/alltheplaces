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
    custom_settings = {
        "USER_AGENT": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36"
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

        template = "https://www.abercrombie.com/api/ecomm/a-ca/storelocator/search?country={country}"

        for country in countries:
            url = template.format(country=country)
            yield scrapy.Request(url, callback=self.parse)

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
