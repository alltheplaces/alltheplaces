import random
import re

from scrapy import Spider
from scrapy.http import JsonRequest
from scrapy.signals import spider_idle

from locations.dict_parser import DictParser
from locations.hours import DAYS, DAYS_EN, OpeningHours, day_range
from locations.items import Feature

# To use this store finder, specify key = x where x is the unique
# identifier of the store finder in domain x.geoapp.me.
#
# It is likely there are additional fields of data worth extracting
# from the store finder. These should be added by overriding the
# parse_item function. Two parameters are passed, item (and ATP
# "Feature" class) and location (a dict which is returned from the
# store locator JSON response for a particular location).
#
# This spider has two crawling steps which are executed in order:
# 1. Obtain list of all locations by using the API to do bounding
#    box searches across the world. The only thing of interest
#    returned for each location in this step is a unique identifier
#    and coordinates.
# 2. Iterating through the all locations list produced by step (1),
#    request the nearest 50 (API limit) locations for each location
#    in the all locations list. Remove from the all locations list
#    and locations that were returned with a nearest location
#    search. Repeat until the all locations list is empty. The
#    nearest location search returns all details of a location.
#
# Note that due to the way the two crawling steps are required to
# operate, numerous duplicate locations will be dropped during
# extraction. It is common for locations to be present in more than
# one nearby cluster of locations that the "nearest to" search
# iterates through.


class GeoMeSpider(Spider):
    key = ""
    api_version = "2"
    url_within_bounds_template = "https://{}.geoapp.me/api/v{}/locations/within_bounds?sw[]={}&sw[]={}&ne[]={}&ne[]={}"
    url_nearest_to_template = "https://{}.geoapp.me/api/v{}/locations/nearest_to?lat={}&lng={}&limit=50"
    locations_found = {}

    def start_requests(self):
        self.crawler.signals.connect(self.start_location_requests, signal=spider_idle)
        yield JsonRequest(
            url=self.url_within_bounds_template.format(self.key, self.api_version, -90, -180, 90, 180),
            callback=self.parse_bounding_box,
        )

    def parse_bounding_box(self, response):
        for cluster in response.json().get("clusters", []):
            if b := cluster.get("bounds"):
                yield JsonRequest(
                    url=self.url_within_bounds_template.format(
                        self.key, self.api_version, b["sw"][0], b["sw"][1], b["ne"][0], b["ne"][1]
                    ),
                    callback=self.parse_bounding_box,
                )
        for location in response.json().get("locations", []):
            self.locations_found[location["id"]] = (float(location["lat"]), float(location["lng"]))

    def start_location_requests(self):
        self.crawler.signals.disconnect(self.start_location_requests, signal=spider_idle)
        self.crawler.engine.crawl(self.get_next_location())

    def parse_locations(self, response):
        for location in response.json()["locations"]:
            # Remove found location from the list of locations which
            # are still waiting to be found.
            if self.locations_found.get(location["id"]):
                self.locations_found.pop(location["id"])

            if location.get("inactive"):
                continue

            location["street_address"] = location.pop("address")
            item = DictParser.parse(location)
            self.extract_hours(item, location)
            yield from self.parse_item(item, location) or []

        # Get the next location to do a "nearest to" search from.
        yield self.get_next_location()

    def get_next_location(self) -> JsonRequest:
        if len(self.locations_found) == 0:
            return
        next_search_location_id = random.choice(list(self.locations_found))
        next_search_location_coords = self.locations_found[next_search_location_id]
        self.locations_found.pop(next_search_location_id)
        return JsonRequest(
            url=self.url_nearest_to_template.format(
                self.key, self.api_version, next_search_location_coords[0], next_search_location_coords[1]
            ),
            callback=self.parse_locations,
            dont_filter=True,
        )

    @staticmethod
    def extract_hours(item: Feature, location: dict):
        item["opening_hours"] = OpeningHours()
        if location.get("open_status") == "twenty_four_hour":
            item["opening_hours"].add_days_range(DAYS, "00:00", "23:59")
            return
        open_hours = location.get("opening_hours")
        if not open_hours:
            return
        hours_string = ""
        for spec in open_hours:
            days = spec["days"]
            day_from = day_to = days[0]
            if len(days) == 2:
                day_to = days[1]
            for day in day_range(DAYS_EN[day_from], DAYS_EN[day_to]):
                for hours in spec["hours"]:
                    start_time = hours[0].replace("1900-01-01 ", "")
                    end_time = re.sub(
                        r"^00:00$", "23:59", hours[1].replace("00:00:00", "23:59:59").replace("1900-01-01 ", "")
                    )
                    hours_string = f"{hours_string} {day}: {start_time} - {end_time}"
        item["opening_hours"].add_ranges_from_string(hours_string)

    def parse_item(self, item: Feature, location: dict, **kwargs):
        yield item
