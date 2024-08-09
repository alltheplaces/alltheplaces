import random

import pygeohash
from chompjs import parse_js_object
from scrapy import Request, Spider
from scrapy.http import JsonRequest, Response
from scrapy.spidermiddlewares.httperror import HttpError

from locations.dict_parser import DictParser
from locations.items import Feature

# Documentation for this Stockist store finder is available at:
# https://help.stockist.co/
#
# To use this store finder, specify the API key using the "key"
# attribute of this class. You may need to define a parse_item
# function to extract additional location data and to make
# corrections to automatically extracted location data.
#
# Note that some brands may have disabled the ability for clients to
# list all locations in a single query. This store finder will
# automatically detect this situation and will use an alternative
# approach of searching for locations by radius searches. No
# additional parameters need to be supplied to this store finder.
# Just note that some additional requests will be required for this
# store finder to return all locations.


class StockistSpider(Spider):
    dataset_attributes = {"source": "api", "api": "stockist.co"}
    key: str = ""
    max_distance: int = 50000
    coordinates_pending: list[tuple[float, float]] = []

    def start_requests(self):
        yield JsonRequest(
            url=f"https://stockist.co/api/v1/{self.key}/locations/all",
            callback=self.parse_all_locations,
            errback=self.parse_all_locations_error,
        )

    def parse_all_locations(self, response: Response):
        for location in response.json():
            yield from self.parse_item(self.parse_location(location), location) or []

    @staticmethod
    def parse_location(location):
        item = DictParser.parse(location)
        item["street_address"] = ", ".join(filter(None, [location["address_line_1"], location["address_line_2"]]))
        return item

    def parse_all_locations_error(self, failure):
        if failure.check(HttpError):
            if failure.value.response.status == 400:
                if "error" in failure.value.response.json().keys():
                    if failure.value.response.json()["error"] == "Method unavailable.":
                        yield Request(
                            url=f"https://stockist.co/api/v1/{self.key}/widget.js", callback=self.parse_search_config
                        )

    def parse_search_config(self, response: Response):
        config = parse_js_object(response.text.split("(", 1)[1].split(");", 1)[0])
        self.max_distance = config["max_distance"]
        yield JsonRequest(
            url=f"https://stockist.co/api/v1/{self.key}/locations/overview.js", callback=self.parse_geohashes
        )

    def parse_geohashes(self, response: Response):
        self.coordinates_pending = [pygeohash.decode(geohash[:-1]) for geohash in response.json()["i"]]
        if len(self.coordinates_pending) > 0:
            yield from self.make_next_search_request()

    def make_next_search_request(self):
        next_coordinates = random.choice(self.coordinates_pending)
        yield JsonRequest(
            url=f"https://stockist.co/api/v1/{self.key}/locations/search?latitude={next_coordinates[0]}&longitude={next_coordinates[1]}&distance={self.max_distance}",
            callback=self.parse_search_results,
        )

    def parse_search_results(self, response: Response):
        for location in response.json()["locations"]:
            yield from self.parse_item(self.parse_location(location), location) or []

            geohash = pygeohash.encode(float(location["latitude"]), float(location["longitude"]), precision=9)
            geohash_coordinates = pygeohash.decode(geohash)
            try:
                self.coordinates_pending.remove(geohash_coordinates)
            except ValueError:
                pass

        if len(self.coordinates_pending) > 0:
            yield from self.make_next_search_request()

    def parse_item(self, item: Feature, location: dict):
        yield item
