import csv

import scrapy

from locations.items import Feature
from locations.searchable_points import open_searchable_points
from locations.spiders.vapestore_gb import clean_address


class BlueRhinoSpider(scrapy.Spider):
    name = "bluerhino"
    item_attributes = {
        "brand": "Blue Rhino",
        "brand_wikidata": "Q65681213",
        "country": "US",
    }
    allowed_domains = ["bluerhino.com"]

    custom_settings = {"DEFAULT_REQUEST_HEADERS": {"Accept": "application/json"}}

    def start_requests(self):
        with open_searchable_points("us_centroids_100mile_radius.csv") as points:
            for point in csv.DictReader(points):
                yield scrapy.Request(
                    f'https://bluerhino.com/api/propane/GetRetailersNearPoint?latitude={point["latitude"]}&longitude={point["longitude"]}&radius=1000&name=&type=&top=5000&cache=false'
                )

    def parse(self, response):
        for row in response.json():
            properties = {
                "lat": row["Latitude"],
                "lon": row["Longitude"],
                "ref": row["RetailKey"],
                "name": row["RetailName"],
                "street_address": clean_address([row["Address1"], row["Address2"], row["Address3"]]),
                "city": row["City"],
                "state": row["State"],
                "postcode": row["Zip"],
                "phone": row["Phone"],
                "extras": {"fax": row["Fax"]},
            }
            yield Feature(**properties)
