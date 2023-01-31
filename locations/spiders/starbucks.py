import csv
import json

import scrapy

from locations.items import GeojsonPointItem
from math import sqrt

HEADERS = {"X-Requested-With": "XMLHttpRequest"}
STORELOCATOR = "https://www.starbucks.com/bff/locations?lat={}&lng={}"

class StarbucksSpider(scrapy.Spider):
    name = "starbucks"
    item_attributes = {"brand": "Starbucks", "brand_wikidata": "Q37158"}
    allowed_domains = ["www.starbucks.com"]

    def start_requests(self):
        searchable_point_files = [
            "./locations/searchable_points/us_centroids_50mile_radius.csv",
            "./locations/searchable_points/ca_centroids_50mile_radius.csv",
        ]

        for point_file in searchable_point_files:
            with open(point_file) as points:
                reader = csv.DictReader(points)
                for point in reader:
                    request = scrapy.Request(
                        url=STORELOCATOR.format(point["latitude"], point["longitude"]),
                        headers=HEADERS,
                        callback=self.parse,
                    )
                    # Distance is in degrees...
                    request.meta["distance"] = 1
                    yield request

    def parse(self, response):
        responseJson = json.loads(response.body)
        stores = responseJson["stores"]

        for store in stores:
            storeLat = store["coordinates"]["latitude"]
            storeLon = store["coordinates"]["longitude"]
            properties = {
                "name": store["name"],
                "street_address": ", ".join(
                    filter(
                        None,
                        [
                            store["address"]["streetAddressLine1"],
                            store["address"]["streetAddressLine2"],
                            store["address"]["streetAddressLine3"],
                        ],
                    )
                ),
                "city": store["address"]["city"],
                "state": store["address"]["countrySubdivisionCode"],
                "country": store["address"]["countryCode"],
                "postcode": store["address"]["postalCode"],
                "phone": store["phoneNumber"],
                "ref": store["id"],
                "lon": storeLon,
                "lat": storeLat,
                "brand": store["brandName"],
                "website": f'https://www.starbucks.com/store-locator/store/{store["id"]}/{store["slug"]}',
                "extras": {"number": store["storeNumber"], "ownership_type": store["ownershipTypeCode"]},
            }
            yield GeojsonPointItem(**properties)

        # Get lat and lng from URL
        pairs = response.url.split("?")[-1].split("&")
        # Center is lng, lat
        center = [float(pairs[1].split("=")[1]), float(pairs[0].split("=")[1])]

        paging = responseJson["paging"]
        if paging["returned"] > 0 and paging["limit"] == paging["returned"]:
            if response.meta["distance"] > 0.10:
                nextDistance = response.meta["distance"] / 2
                nextDistanceCorner = nextDistance * (sqrt(2)/2)
                # Create eight new coordinate pairs
                nextCoordinates = [
                    [center[0] - nextDistanceCorner, center[1] + nextDistanceCorner],
                    [center[0] + nextDistanceCorner, center[1] + nextDistanceCorner],
                    [center[0] - nextDistanceCorner, center[1] - nextDistanceCorner],
                    [center[0] + nextDistanceCorner, center[1] - nextDistanceCorner],
                    [center[0] - nextDistance, center[1]],
                    [center[0] + nextDistance, center[1]],
                    [center[0], center[1] - nextDistance],
                    [center[0], center[1] + nextDistance],
                ]
                urls = [STORELOCATOR.format(c[1], c[0]) for c in nextCoordinates]
                for url in urls:
                    request = scrapy.Request(url=url, headers=HEADERS, callback=self.parse)
                    request.meta["distance"] = nextDistance
                    yield request
