import csv
import re

import scrapy

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.searchable_points import open_searchable_points


class StarbucksEUSpider(scrapy.Spider):
    name = "starbucks_eu"
    item_attributes = {"brand": "Starbucks", "brand_wikidata": "Q37158"}
    allowed_domains = ["starbucks.co.uk"]

    def start_requests(self):
        base_url = "https://www.starbucks.co.uk/api/v1/store-finder?latLng={lat}%2C{lon}"

        with open_searchable_points("eu_centroids_20km_radius_country.csv") as points:
            reader = csv.DictReader(points)
            for point in reader:
                yield scrapy.http.Request(
                    url=base_url.format(lat=point["latitude"], lon=point["longitude"]),
                    callback=self.parse,
                )

    def parse(self, response):
        data = response.json()

        for place in data["stores"]:
            try:
                street, postal_city = place["address"].strip().split("\n")
            except:
                street, addr_2, postal_city = place["address"].strip().split("\n")

            # https://github.com/alltheplaces/alltheplaces/pull/8993#issuecomment-2254338471
            # starbucks_eu.geojson has "addr:full": "undefined, BA11 4QE Frome", "addr:street_address": "undefined"
            if street.lower() == "undefined":
                street = None

            try:
                city_hold = re.search(
                    r"\s([A-Z]{1,2}[a-z]*)$|\s([A-Z]{1}[a-z]*)(\s|,\s)([A-Z]{1,2}[a-z]*)$|\s([A-Z]{1}[a-z]*)\s([0-9]*)$",
                    postal_city,
                ).groups()
                res = [i for i in city_hold if i]

                if ", " in res:
                    city = "".join(res)
                else:
                    city = " ".join(res)

                postal = postal_city.replace(city, "").strip()
            except:
                city = postal_city
                postal = postal_city

            drivethrough = "no"
            app = "no"
            wifi = "no"
            for am in place["amenities"]:
                if am["type"] == "car":
                    drivethrough = "yes"
                elif am["type"] == "mobile-order-pay":
                    app = "yes"
                elif am["type"] == "wifi":
                    wifi = "wlan"

            properties = {
                "ref": place["id"],
                "name": place["name"],
                "street_address": street,
                "city": city,
                "postcode": postal,
                "addr_full": place["address"].strip().replace("\n", ", "),
                "lat": place["coordinates"]["lat"],
                "lon": place["coordinates"]["lng"],
                "phone": place["phoneNumber"],
                "extras": {
                    "drive_through": drivethrough,
                    "payment:app": app,
                    "internet_access": wifi,
                },
            }

            apply_category(Categories.COFFEE_SHOP, properties)

            yield Feature(**properties)
