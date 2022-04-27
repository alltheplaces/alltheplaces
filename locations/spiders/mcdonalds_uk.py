# -*- coding: utf-8 -*-
import csv

import scrapy

from locations.items import GeojsonPointItem


class McDonaldsUKSpider(scrapy.Spider):
    name = "mcdonalds_uk"
    item_attributes = {"brand": "McDonald's", "brand_wikidata": "Q38076"}
    allowed_domains = ["mcdonalds.com"]
    download_delay = 2

    def start_requests(self):
        url = "https://www.mcdonalds.com/googleappsv2/geolocation?latitude={lat}&longitude={lng}&radius=120&maxResults=300&country=gb&language=en-gb&showClosed=true"
        with open(
            "./locations/searchable_points/eu_centroids_120km_radius_country.csv"
        ) as points:
            reader = csv.DictReader(points)
            for point in reader:
                if point["country"] == "UK":
                    yield scrapy.Request(
                        url=url.format(lat=point["latitude"], lng=point["longitude"]),
                        callback=self.parse,
                    )

    def parse(self, response):
        data = response.json()
        for store in data["features"]:
            if "identifierValue" not in store["properties"].keys():
                continue
            else:
                properties = {
                    "website": "https://www.mcdonalds.com/gb/en-gb/location/"
                    + self.urlify(store["properties"]["addressLine3"])
                    + "/"
                    + self.urlify(store["properties"]["longDescription"])
                    + "/"
                    + self.urlify(store["properties"]["addressLine1"])
                    + "/"
                    + store["properties"]["identifierValue"]
                    + ".html",
                    "ref": store["properties"]["id"],
                    "name": store["properties"]["name"],
                    "street_address": store["properties"]["addressLine1"],
                    "city": store["properties"]["addressLine3"],
                    "postcode": store["properties"]["postcode"],
                    "country": "GB",
                    "addr_full": ", ".join(
                        filter(
                            None,
                            (
                                store["properties"]["addressLine1"],
                                store["properties"]["addressLine3"],
                                store["properties"]["postcode"],
                                "United Kingdom",
                            ),
                        ),
                    ),
                    "phone": "+44 " + store["properties"]["telephone"][1:],
                    "lat": float(store["geometry"]["coordinates"][1]),
                    "lon": float(store["geometry"]["coordinates"][0]),
                    "opening_hours": "; ".join(
                        (
                            "Mo "
                            + (
                                store["properties"]["restauranthours"]["hoursMonday"]
                                if "hoursMonday"
                                in store["properties"]["restauranthours"]
                                else "off"
                            ),
                            "Tu "
                            + (
                                store["properties"]["restauranthours"]["hoursTuesday"]
                                if "hoursTuesday"
                                in store["properties"]["restauranthours"]
                                else "off"
                            ),
                            "We "
                            + (
                                store["properties"]["restauranthours"]["hoursWednesday"]
                                if "hoursWednesday"
                                in store["properties"]["restauranthours"]
                                else "off"
                            ),
                            "Th "
                            + (
                                store["properties"]["restauranthours"]["hoursThursday"]
                                if "hoursThursday"
                                in store["properties"]["restauranthours"]
                                else "off"
                            ),
                            "Fr "
                            + (
                                store["properties"]["restauranthours"]["hoursFriday"]
                                if "hoursFriday"
                                in store["properties"]["restauranthours"]
                                else "off"
                            ),
                            "Sa "
                            + (
                                store["properties"]["restauranthours"]["hoursSaturday"]
                                if "hoursSaturday"
                                in store["properties"]["restauranthours"]
                                else "off"
                            ),
                            "Su "
                            + (
                                store["properties"]["restauranthours"]["hoursSunday"]
                                if "hoursSunday"
                                in store["properties"]["restauranthours"]
                                else "off"
                            ),
                        )
                    )
                    .replace(" - ", "-")
                    .replace("-00:00", "-24:00")
                    .replace("-23:59", "-24:00")
                    if "restauranthours" in store["properties"].keys()
                    else "",
                }

                yield GeojsonPointItem(**properties)

    def urlify(self, str):
        return (
            str.lower()
            .replace(" ", "-")
            .replace("/", "")
            .replace(",", "")
            .replace("&", "")
            .replace("'", "")
            .replace("(", "")
            .replace(")", "")
            .replace(".", "")
        )
