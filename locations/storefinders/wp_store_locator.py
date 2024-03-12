import logging

from scrapy import Selector, Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.geo import point_locations
from locations.hours import DAYS_BY_FREQUENCY, OpeningHours, sanitise_day
from locations.items import Feature
from locations.spiders.vapestore_gb import clean_address

# Source code for the WP Store Locator API call used by this spider:
# https://github.com/wp-plugins/wp-store-locator/blob/master/frontend/wpsl-ajax-functions.php
#
# There are two ways to use this spider:
# 1. Attempt to return all locations with a single query.
#      Specify allowed_domains = [x, y, ..] (either one or more
#      domains such as example.net) and the default path for the WP
#      Store Locator API endpoint will be used. In the event the
#      default path is different, you can alternatively specify one
#      or more start_urls = [x, y, ..].
# 2. Perform a geographic radius search with multiple queries.
#      In addition to method (1), also supply a list of searchable
#      points files as searchable_points_files = [x, y..] and also
#      specify a non-zero number for search_radius = x and
#      max_results = x. The max_results parameter is hard-coded in
#      server configuration and cannot be changed. No radius search
#      should return max_results locations because this is a sign
#      that some locations are being truncated.
#
#      An exception will be raised if max_results (or more)
#      locations are returned in any given radius search, as this
#      indicates some locations have been truncated. If this occurs,
#      more granular searchable points files need to be supplied,
#      and search_raidus needs to be selected carefully to ensure
#      that max_results (or more) locations are never returned for
#      any radius search.
#
# If clean ups or additional field extraction is required from the
# source data, override the parse_item function. Two parameters are
# passed, item (an ATP "Feature" class) and location (a dict which
# is returned from the store locator JSON response for a particular
# location).


class WPStoreLocatorSpider(Spider):
    days = None
    time_format = "%H:%M"
    searchable_points_files = []
    search_radius = 0
    max_results = 0
    possible_days = DAYS_BY_FREQUENCY

    def start_requests(self):
        if len(self.start_urls) == 0 and hasattr(self, "allowed_domains"):
            for domain in self.allowed_domains:
                if len(self.searchable_points_files) > 0 and self.search_radius != 0 and self.max_results != 0:
                    for searchable_points_file in self.searchable_points_files:
                        for lat, lon in point_locations(searchable_points_file):
                            yield JsonRequest(
                                url=f"https://{domain}/wp-admin/admin-ajax.php?action=store_search&lat={lat}&lng={lon}&max_results={self.max_results}&search_radius={self.search_radius}"
                            )
                else:
                    yield JsonRequest(url=f"https://{domain}/wp-admin/admin-ajax.php?action=store_search&autoload=1")
        elif len(self.start_urls) != 0:
            for url in self.start_urls:
                if len(self.searchable_points_files) > 0 and self.search_radius != 0 and self.max_results != 0:
                    for searchable_points_file in self.searchable_points_files:
                        for lat, lon in point_locations(searchable_points_file):
                            yield JsonRequest(
                                url=f"{url}&lat={lat}&lng={lon}&max_results={self.max_results}&search_radius={self.search_radius}"
                            )
                else:
                    yield JsonRequest(url=url)

    def parse(self, response, **kwargs):
        if self.max_results != 0 and len(response.json()) >= self.max_results:
            raise RuntimeError(
                "Locations have probably been truncated due to max_results (or more) locations being returned by a single geographic radius search. Use more granular searchable_points_files and a smaller search_radius."
            )
        for location in response.json():
            item = DictParser.parse(location)
            item["street_address"] = clean_address([location.get("address"), location.get("address2")])
            item["name"] = location["store"]
            # If we have preconfigured the exact days to use, start there
            if self.days is not None:
                item["opening_hours"] = self.parse_opening_hours(location, self.days)
            else:
                # Otherwise, iterate over the possibilities until we get a first match
                logging.warning(
                    "Attempting to detect opening hours - specify self.days = DAYS_EN or the appropriate language code to suppress this warning"
                )
                for days in self.possible_days:
                    item["opening_hours"] = self.parse_opening_hours(location, days)
                    if item["opening_hours"] is not None:
                        self.days = days
                        break

            yield from self.parse_item(item, location) or []

    def parse_item(self, item: Feature, location: dict, **kwargs):
        yield item

    def parse_opening_hours(self, location: dict, days: dict, **kwargs) -> OpeningHours:
        if not location.get("hours"):
            return
        sel = Selector(text=location["hours"])
        oh = OpeningHours()
        for rule in sel.xpath("//tr"):
            day = sanitise_day(rule.xpath("./td/text()").get(), days)
            times = rule.xpath("./td/time/text()").get()
            if not day or not times:
                continue
            if times.lower() in ["closed"]:
                continue
            start_time, end_time = times.split("-")
            oh.add_range(day, start_time.strip(), end_time.strip(), time_format=self.time_format)

        return oh
