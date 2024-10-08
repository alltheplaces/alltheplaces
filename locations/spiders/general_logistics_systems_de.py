import csv

import scrapy

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.searchable_points import open_searchable_points

HEADERS = {"X-Requested-With": "XMLHttpRequest"}
STORELOCATOR = "https://api.gls-pakete.de/parcelshops?latitude={:0.5}&longitude={:0.5}&distance=40"


class GeneralLogisticsSystemsDESpider(scrapy.Spider):
    name = "general_logistics_systems_de"
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
        pois = response.json().get("shops")

        for poi in pois:
            item = DictParser.parse(poi)
            address = poi["address"]
            coordinates = address["coordinates"]
            item["lat"] = coordinates["latitude"]
            item["lon"] = coordinates["longitude"]
            item["name"] = address["name"]
            opening_hours = OpeningHours()
            for day, time_ranges in poi["openingHours"].items():
                for time_range in time_ranges:
                    opening_hours.add_range(day, time_range["from"], time_range["to"])

            item["opening_hours"] = opening_hours.as_opening_hours()
            yield item
