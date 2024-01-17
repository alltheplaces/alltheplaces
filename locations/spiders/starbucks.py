import csv
import json
from collections import defaultdict
from math import sqrt

import scrapy

from locations.categories import Categories
from locations.items import Feature
from locations.searchable_points import open_searchable_points

HEADERS = {"X-Requested-With": "XMLHttpRequest"}
STORELOCATOR = "https://www.starbucks.com/bff/locations?lat={}&lng={}"


class StarbucksSpider(scrapy.Spider):
    name = "starbucks"
    item_attributes = {"brand": "Starbucks", "brand_wikidata": "Q37158", "extras": Categories.COFFEE_SHOP.value}
    allowed_domains = ["www.starbucks.com"]

    def start_requests(self):
        searchable_point_files = [
            "us_centroids_50mile_radius.csv",
            "ca_centroids_50mile_radius.csv",
        ]

        for point_file in searchable_point_files:
            with open_searchable_points(point_file) as points:
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
        response_json = json.loads(response.body)
        stores = response_json["stores"]

        for store in stores:
            store_lat = store["coordinates"]["latitude"]
            store_lon = store["coordinates"]["longitude"]
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
                "lon": store_lon,
                "lat": store_lat,
                "brand": store["brandName"],
                "website": f'https://www.starbucks.com/store-locator/store/{store["id"]}/{store["slug"]}',
                "extras": {"number": store["storeNumber"], "ownership_type": store["ownershipTypeCode"]},
            }
            yield Feature(**properties)

        # Get lat and lng from URL
        pairs = response.url.split("?")[-1].split("&")
        # Center is lng, lat
        center = [float(pairs[1].split("=")[1]), float(pairs[0].split("=")[1])]

        paging = response_json["paging"]
        if paging["returned"] > 0 and paging["limit"] == paging["returned"]:
            if response.meta["distance"] > 0.15:
                next_distance = response.meta["distance"] / 2
                # Create four new coordinate pairs
                next_coordinates = [
                    [center[0] - next_distance, center[1] + next_distance],
                    [center[0] + next_distance, center[1] + next_distance],
                    [center[0] - next_distance, center[1] - next_distance],
                    [center[0] + next_distance, center[1] - next_distance],
                ]
                urls = [STORELOCATOR.format(c[1], c[0]) for c in next_coordinates]
                for url in urls:
                    request = scrapy.Request(url=url, headers=HEADERS, callback=self.parse)
                    request.meta["distance"] = next_distance
                    yield request

            elif response.meta["distance"] > 0.10:
                # Only used to track how often this happens
                self.logger.debug("Using secondary search of far away stores")
                next_distance = response.meta["distance"] / 2

                next_coordinates = []
                current_center = center
                additional_stores = 5
                store_distances = defaultdict(list)

                # Loop through to find 5 more stores
                for ii in range(additional_stores):
                    # Find distance between current center and all stores
                    for jj, store in enumerate(stores):
                        store_lat = store["coordinates"]["latitude"]
                        store_lon = store["coordinates"]["longitude"]
                        store_distances[jj].append(
                            sqrt((current_center[1] - store_lat) ** 2 + (current_center[0] - store_lon) ** 2)
                        )

                    # Find total distance from each store to each center point
                    total_distances = {key: sum(val) for key, val in store_distances.items()}

                    # Find store furthest away
                    max_store = max(total_distances, key=total_distances.get)
                    # Replace current center
                    current_center = [
                        stores[max_store]["coordinates"]["longitude"],
                        stores[max_store]["coordinates"]["latitude"],
                    ]

                    # Append it to the next search list
                    next_coordinates.append(
                        [stores[max_store]["coordinates"]["longitude"], stores[max_store]["coordinates"]["latitude"]]
                    )

                urls = [STORELOCATOR.format(c[1], c[0]) for c in next_coordinates]
                for url in urls:
                    self.logger.debug(f"Adding {url} to list")

                    request = scrapy.Request(url=url, headers=HEADERS, callback=self.parse)
                    request.meta["distance"] = next_distance
                    yield request
