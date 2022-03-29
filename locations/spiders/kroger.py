# -*- coding: utf-8 -*-
import scrapy

from locations.hours import OpeningHours
from locations.items import GeojsonPointItem
from scrapy.selector import Selector

WIKIBRANDS = {
    "Baker's": "Q4849080",
    "City Market": "Q5123299",
    "Dillons": "Q5276954",
    "Food 4 Less": "Q5465282",
    "Foods Co": "Q5465282",
    "Fred Meyer": "Q5495932",
    "Fry's Food Stores": "Q5506547",
    "Gerbes": "Q5276954",
    "JayC": "Q6166302",
    "King Soopers": "Q6412065",
    "Kroger": "Q153417",
    "Mariano's Fresh Market": "Q55622168",
    "Metro Market": "Q7371288",
    "Pay Less": "Q7156587",
    "Owen's": "Q7114367",
    "Pick 'n Save": "Q7371288",
    "QFC": "Q7265425",
    "Ralphs": "Q3929820",
    "Smith's": "Q7544856",
}


class KrogerSpider(scrapy.Spider):
    name = "kroger"
    allowed_domains = ["www.kroger.com"]
    custom_settings = {
        "USER_AGENT": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36"
    }

    def start_requests(self):
        base_url = "https://www.kroger.com/atlas/v1/stores/v1/search?filter.latLng={lat},{lng}&filter.radiusInMiles=30"

        with open(
            "./locations/searchable_points/us_centroids_25mile_radius.csv"
        ) as points:
            next(points)  # Ignore the header
            for point in points:
                _, lat, lon = point.strip().split(",")

                url = base_url.format(lat=lat, lng=lon)

                yield scrapy.http.Request(url=url, method="GET", callback=self.parse)

    def parse(self, response):
        data = response.json()

        for store in data["data"]["storeSearch"]["results"]:
            try:
                brand = store["facilityName"]
            except:
                brand = store["brand"]
            try:
                wiki = WIKIBRANDS.get(brand)
            except:
                wiki = ""

            properties = {
                "ref": store["locationId"],
                "name": store["vanityName"],
                "addr_full": store["address"]["address"]["addressLines"][0],
                "city": store["address"]["address"]["cityTown"],
                "state": store["address"]["address"]["stateProvince"],
                "postcode": store["address"]["address"]["postalCode"],
                "country": store["address"]["address"]["countryCode"],
                "lat": store["location"]["lat"],
                "lon": store["location"]["lng"],
                "brand": brand,
                "brand_wikidata": wiki,
            }

            yield GeojsonPointItem(**properties)
