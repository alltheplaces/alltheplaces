from typing import Iterable

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.geo import country_iseadgg_centroids, point_locations
from locations.hours import OpeningHours
from locations.items import Feature, SocialMedia, set_social_media


class StoreRocketSpider(Spider):
    """
    StoreRocket is a map based JSON API driven store locator.
    https://storerocket.io/

    To use, specify:
      - `storerocket_id`: mandatory parameter
      - `base_url`: optional parameter, sets the base URL for individual
        location pages (which may be provided as a URL slug by this API)
      - `time_hours_format`: optional parameter that is '24' by default and
        can be changed to '12' if the opening hours are specified in 12 hr
        time notation (e.g. 2:00 AM). This attribute is used in determining
        whether to replace "24 HOURS" with a 24h or 12h time notation range.

    Some StoreRocket accounts will not return all features at once in a
    single API call. If this is the case, there are two alternative methods
    available for use of this storefinder:

    PREFERRED
    1. Supply a list of ISO-3166 alpha-2 country codes as the
       iseadgg_countries_list parameter and a suitable non-zero search_radius
       value in miles. The API only accepts a pre-configured set of search
       radiuses and these change per StoreRocket account. Check the store
       finder page for a drop-down box listing valid search radius values.

       Example:
         iseadgg_countries_list = ["US", "CA"]
         search_radius = 100

         In this example, a 158km ISEADGG centroid grid will automatically
         be selected as the most appropriate to use against a 100mi search
         radius accepted by the API endpoint.

    NONPREFERRED
    2. Supply a list of searchable_points_files = [x, y..] suitable for use
       with the point_locations function of locations.geo and a suitable
       non-zero search_radius value in miles. The API only accepts a
       pre-configured set of search radiuses and these change per StoreRocket
       account. Check the store finder page for a drop-down box listing valid
       search radius values.
    """

    dataset_attributes = {"source": "api", "api": "storerocket.io"}
    storerocket_id: str = ""
    base_url: str | None = None
    time_hours_format: str = 24  # or 12
    iseadgg_countries_list: list[str] = []
    searchable_points_files: list[str] = []
    search_radius: int = 0
    max_results: int = 1000

    def start_requests(self) -> Iterable[JsonRequest]:
        if len(self.iseadgg_countries_list) == 0 and len(self.searchable_points_files) == 0:
            # PREFERRED approach of requesting all features at once in a
            # single API call. Note that some StoreRocket instances enforce a
            # maximum number of results returned and if this is the case, a
            # geographic search method is required to be used.
            yield JsonRequest(url=f"https://storerocket.io/api/user/{self.storerocket_id}/locations")
        elif len(self.iseadgg_countries_list) > 0 and self.search_radius != 0 and self.max_results != 0:
            # SECOND PREFERENCE geographic radius search method using ISEADGG
            # centroids for a supplied list of ISO-3166 alpha-2 country codes.
            if self.search_radius >= 285:
                iseadgg_radius = 458
            elif self.search_radius >= 200:
                iseadgg_radius = 315
            elif self.search_radius >= 100:
                iseadgg_radius = 158
            elif self.search_radius >= 60:
                iseadgg_radius = 94
            elif self.search_radius >= 50:
                iseadgg_radius = 79
            elif self.search_radius >= 30:
                iseadgg_radius = 48
            elif self.search_radius >= 15:
                iseadgg_radius = 24
            else:
                raise RuntimeError(
                    "A minimum search_radius of 15 (miles) is required to be used for the ISEADGG geographic radius search method."
                )
            for lat, lon in country_iseadgg_centroids(self.iseadgg_countries_list, iseadgg_radius):
                yield JsonRequest(
                    url=f"https://storerocket.io/api/user/{self.storerocket_id}/locations?lat={lat}&lng={lon}&radius={self.search_radius}&limit={self.max_results}"
                )
        elif len(self.searchable_points_files) > 0 and self.search_radius != 0 and self.max_results != 0:
            # THIRD PREFERENCE geographic radius search method using a manually
            # specified list of searchable_points_file containing centroids.
            for searchable_points_file in self.searchable_points_files:
                for lat, lon in point_locations(searchable_points_file):
                    yield JsonRequest(
                        url=f"https://storerocket.io/api/user/{self.storerocket_id}/locations?lat={lat}&lng={lon}&radius={self.search_radius}&limit={self.max_results}"
                    )

    def parse(self, response, **kwargs) -> Iterable[Feature]:
        if not response.json()["success"]:
            return

        locations = response.json()["results"]["locations"]

        if len(self.iseadgg_countries_list) != 0 or len(self.searchable_points_files) != 0:
            if len(locations) >= self.max_results:
                raise RuntimeError(
                    "Locations have probably been truncated due to max_results (or more) locations being returned by a single geographic radius search. Use a smaller search_radius."
                )

            if len(locations) > 0:
                self.crawler.stats.inc_value("atp/geo_search/hits")
            else:
                self.crawler.stats.inc_value("atp/geo_search/misses")
            self.crawler.stats.max_value("atp/geo_search/max_features_returned", len(locations))

        for location in locations:
            self.pre_process_data(location)
            item = DictParser.parse(location)

            item["street_address"] = ", ".join(filter(None, [location["address_line_1"], location["address_line_2"]]))
            item["email"] = location.get("email")

            set_social_media(item, SocialMedia.FACEBOOK, location.get("facebook"))
            set_social_media(item, SocialMedia.INSTAGRAM, location.get("instagram"))
            set_social_media(item, SocialMedia.TWITTER, location.get("twitter"))

            if self.base_url:
                item["website"] = f'{self.base_url}?location={location["slug"]}'

            item["opening_hours"] = OpeningHours()
            hours_string = ""
            for day_name, day_hours in location["hours"].items():
                hours_string = hours_string + f" {day_name}: {day_hours}"
            if self.time_hours_format == 24:
                hours_string = hours_string.upper().replace("24 HOURS", "00:00 - 23:59")
            else:
                hours_string = hours_string.upper().replace("24 HOURS", "12:00 AM - 11:59 PM")
            item["opening_hours"].add_ranges_from_string(hours_string)

            yield from self.parse_item(item, location) or []

    def parse_item(self, item: Feature, location: dict, **kwargs) -> Iterable[Feature]:
        yield item

    def pre_process_data(self, location, **kwargs) -> None:
        """Override with any pre-processing on the item."""
