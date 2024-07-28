import csv
from collections import defaultdict
from math import sqrt

from scrapy import Request, Spider

from locations.categories import Categories
from locations.hours import DAYS_EN, OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address
from locations.searchable_points import open_searchable_points

HEADERS = {"X-Requested-With": "XMLHttpRequest"}
STORELOCATOR = "https://www.starbucks.com/bff/locations?lat={}&lng={}"


class StarbucksUSSpider(Spider):
    name = "starbucks_us"
    item_attributes = {"brand": "Starbucks", "brand_wikidata": "Q37158", "extras": Categories.COFFEE_SHOP.value}
    allowed_domains = ["www.starbucks.com"]
    searchable_point_files = ["us_centroids_50mile_radius.csv"]
    country_filter = ["US"]

    def start_requests(self):
        for point_file in self.searchable_point_files:
            with open_searchable_points(point_file) as points:
                reader = csv.DictReader(points)
                for point in reader:
                    request = Request(
                        url=STORELOCATOR.format(point["latitude"], point["longitude"]),
                        headers=HEADERS,
                        callback=self.parse,
                    )
                    # Distance is in degrees...
                    request.meta["distance"] = 1
                    yield request

    def parse(self, response):
        stores = response.json()

        for poi in stores:
            store = poi["store"]

            if store["address"]["countryCode"] not in self.country_filter:
                # Coordinate searches return cross-border results. A country
                # filter ensures that multiple Starbucks spiders for nearby
                # countries don't return the same location.
                continue

            store_lat = store.get("coordinates", {}).get("latitude")
            store_lon = store.get("coordinates", {}).get("longitude")

            properties = {
                "name": store["name"],
                "branch": store["name"],
                "street_address": clean_address(
                    [
                        store["address"]["streetAddressLine1"],
                        store["address"]["streetAddressLine2"],
                        store["address"]["streetAddressLine3"],
                    ],
                ),
                "city": store["address"]["city"],
                "state": store["address"]["countrySubdivisionCode"],
                "country": store["address"]["countryCode"],
                "postcode": store["address"]["postalCode"],
                "phone": store["phoneNumber"],
                "ref": store["id"],
                "lon": store_lon,
                "lat": store_lat,
                "website": f'https://www.starbucks.com/store-locator/store/{store["id"]}/{store["slug"]}',
                "extras": {"number": store["storeNumber"], "ownership_type": store["ownershipTypeCode"]},
            }
            item = Feature(**properties)
            self.parse_hours(item, store)
            yield item

        # Get lat and lng from URL
        pairs = response.url.split("?")[-1].split("&")
        # Center is lng, lat
        center = [float(pairs[1].split("=")[1]), float(pairs[0].split("=")[1])]

        if stores:
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
                    request = Request(url=url, headers=HEADERS, callback=self.parse)
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
                        store_lat = store.get("coordinates", {}).get("latitude")
                        store_lon = store.get("coordinates", {}).get("longitude")
                        if store_lat is None or store_lon is None:
                            continue
                        store_distances[jj].append(
                            sqrt((current_center[1] - store_lat) ** 2 + (current_center[0] - store_lon) ** 2)
                        )

                    # Find total distance from each store to each center point
                    total_distances = {key: sum(val) for key, val in store_distances.items()}

                    if not total_distances:
                        continue

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

                    request = Request(url=url, headers=HEADERS, callback=self.parse)
                    request.meta["distance"] = next_distance
                    yield request

    def parse_hours(self, item: Feature, poi: dict):
        if schedule := poi.get("schedule"):
            try:
                oh = OpeningHours()
                for day in schedule:
                    if not day.get("open"):
                        continue
                    day_name = day.get("dayOfWeek", "")
                    hours_formatted = day.get("hoursFormatted", "")
                    if hours_formatted == "Open 24 hours":
                        oh.add_range(day=DAYS_EN.get(day_name.title()), open_time="00:00", close_time="23:59")
                    else:
                        hours = hours_formatted.split(" to ")
                        oh.add_range(
                            day=DAYS_EN.get(day_name.title()),
                            open_time=hours[0],
                            close_time=hours[1],
                            time_format="%I:%M %p",
                        )
                item["opening_hours"] = oh.as_opening_hours()
            except Exception as e:
                self.logger.warning(f"Failed to parse hours for {schedule}: {e}")
                self.crawler.stats.inc_value(f"atp/{self.name}/hours/failed")
