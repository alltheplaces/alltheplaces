import csv

import scrapy

from locations.items import GeojsonPointItem

HEADERS = {"X-Requested-With": "XMLHttpRequest"}
STORELOCATOR = "https://api.gls-pakete.de/parcelshops?version=4&coordinates={:0.5},{:0.5}&distance=40"


class GeneralLogisticsSystemsSpider(scrapy.Spider):
    name = "gls_de"
    allowed_domains = ["gls-pakete.de"]
    item_attributes = {
        "brand": "General Logistics Systems",
        "brand_wikidata": "Q46495823",
        "country": "DE",
    }

    def start_requests(self):
        searchable_point_files = [
            "./locations/searchable_points/eu_centroids_40km_radius_country.csv",
        ]

        for point_file in searchable_point_files:
            with open(point_file) as openFile:
                results = csv.DictReader(openFile)
                for result in results:
                    if result["country"] == "DE":
                        longitude = float(result["longitude"])
                        latitude = float(result["latitude"])
                        request = scrapy.Request(
                            url=STORELOCATOR.format(latitude, longitude),
                            headers=HEADERS,
                            callback=self.parse,
                        )
                        yield request

    def parse(self, response):
        first_results = response.json()
        results = first_results["shops"]

        for result in results:
            item = GeojsonPointItem()
            address = result["address"]
            phone = result["phone"]
            coordinates = address["coordinates"]
            longitude = coordinates["longitude"]
            latitude = coordinates["latitude"]
            name = address["name"]
            opening_hours = result["openingHours"]

            item["ref"] = result["id"]
            item["name"] = name
            item["lat"] = latitude
            item["lon"] = longitude
            item["street"] = address["street"]
            item["housenumber"] = address["houseNumber"]
            item["city"] = address["city"]
            item["postcode"] = address["postalCode"]
            item["phone"] = phone["number"]
            item["opening_hours"] = opening_hours
            yield item
