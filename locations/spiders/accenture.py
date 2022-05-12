# -*- coding: utf-8 -*-
import json

import scrapy

from locations.items import GeojsonPointItem

countries = [
    "Argentina",
    "Australia",
    "Austria",
    "Belgium",
    "Brazil",
    "Canada",
    "Chile",
    "China",
    "Colombia",
    "Costa Rica",
    "Czech Republic",
    "Denmark",
    "Finland",
    "France",
    "Germany",
    "Greece",
    "Hungary",
    "India",
    "Indonesia",
    "Ireland",
    "Israel",
    "Italy",
    "Japan",
    "Latvia",
    "Luxembourg",
    "Malaysia",
    "Mauritius",
    "Mexico",
    "Morocco",
    "Netherlands",
    "New Zealand",
    "Norway",
    "Peru",
    "Philippines",
    "Poland",
    "Portugal",
    "Romania",
    "Russia",
    "Saudi Arabia",
    "Singapore",
    "Slovak Republic",
    "South Africa",
    "Spain",
    "Sweden",
    "Switzerland",
    "Thailand",
    "Turkey",
    "United Arab Emirates",
    "United Kingdom",
    "United States",
]


class AccentureSpider(scrapy.Spider):
    name = "accenture"
    item_attributes = {"brand": "Accenture", "brand_wikidata": "Q29123313"}
    allowed_domains = ["accenture.com"]
    start_urls = [
        "https://www.accenture.com/us-en/about/location-index",
    ]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def start_requests(self):
        template = "https://www.accenture.com/api/sitecore/LocationsHeroModule/GetLocation?query={country}&from=0&size=150&language=en"

        headers = {
            "Accept": "application/json",
        }

        for country in countries:
            yield scrapy.http.FormRequest(
                url=template.format(country=country),
                method="GET",
                headers=headers,
                callback=self.parse,
            )

    def parse(self, response):
        jsonresponse = response.json()
        data = jsonresponse["documents"]

        for stores in data:
            store = json.dumps(stores)
            store_data = json.loads(store)

            properties = {
                "name": store_data["LocationName"],
                "ref": store_data["LocationName"],
                "addr_full": store_data["Address"],
                "city": store_data["CityName"],
                "state": store_data["StateCode"],
                "postcode": store_data["PostalZipCode"],
                "country": store_data["Country"],
                "phone": store_data.get("ContactTel"),
                "lat": float(store_data["Latitude"]),
                "lon": float(store_data["Longitude"]),
                "website": store_data.get("LocationURL"),
            }

            yield GeojsonPointItem(**properties)
