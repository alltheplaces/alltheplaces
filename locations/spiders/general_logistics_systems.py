import csv

import scrapy

from locations.hours import OpeningHours
from locations.items import Feature
from locations.searchable_points import open_searchable_points

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
            "eu_centroids_40km_radius_country.csv",
        ]

        for point_file in searchable_point_files:
            with open_searchable_points(point_file) as open_file:
                results = csv.DictReader(open_file)
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
            item = Feature()
            address = result["address"]
            phone = result["phone"]
            coordinates = address["coordinates"]
            longitude = coordinates["longitude"]
            latitude = coordinates["latitude"]
            name = address["name"]
            opening_hours = OpeningHours()
            for day, time_ranges in result["openingHours"].items():
                for time_range in time_ranges:
                    opening_hours.add_range(day, time_range["from"], time_range["to"])

            item["ref"] = result["id"]
            item["name"] = name
            item["lat"] = latitude
            item["lon"] = longitude
            item["street"] = address["street"]
            item["housenumber"] = address["houseNumber"]
            item["city"] = address["city"]
            item["postcode"] = address["postalCode"]
            item["phone"] = phone["number"]
            item["opening_hours"] = opening_hours.as_opening_hours()
            yield item
