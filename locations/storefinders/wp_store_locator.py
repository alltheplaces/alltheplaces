import html
from typing import AsyncIterator, Iterable

from scrapy import Selector, Spider
from scrapy.http import JsonRequest, TextResponse

from locations.dict_parser import DictParser
from locations.geo import country_iseadgg_centroids, point_locations
from locations.hours import DAYS_BY_FREQUENCY, OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class WPStoreLocatorSpider(Spider):
    """
    Source code for the WP Store Locator API call used by this spider:
    https://github.com/wp-plugins/wp-store-locator/blob/master/frontend/wpsl-ajax-functions.php

    There are two ways to use this spider:

    PREFERRED
    1. Attempt to return all locations with a single query.

    Specify allowed_domains = ["example.net"] and the default path for the WP
    Store Locator API endpoint will be used. In the event the default path is
    different, you can alternatively specify start_urls =
    ["https://www.example.net/custom-path/wp-admin/admin-ajax.php?action=
      store_search&autoload=1"]

    This method is sometimes restricted by the configuration of the API
    endpoint, requiring the aforesaid geographic radius search method to be
    used instead.

    NONPREFERRED
    2. Perform a geographic radius search with multiple queries.

    In addition to method (1), also supply either:

        PREFERRED
        a. A list of ISO-3166 alpha-2 country codes as the
           iseadgg_countries_list parameter and a suitable non-zero
           search_radius value in kilometres.

           Example:
             iseadgg_countries_list = ["US", "CA"]
             search_radius = 100

           In this example, a 94km ISEADGG centroid grid will automatically be
           selected as the most appropriate to use against a 100km search
           radius accepted by the API endpoint.

        NONPREFERRED
        b. A list of searchable_points_files = [x, y..] suitable for use with
           the point_locations function of locations.geo and a suitable
           non-zero search_radius value in kilometres.

    The max_results parameter is hard-coded in server configuration and cannot
    be changed. No radius search should return max_results locations because
    this is a sign that some locations are being truncated.

    An exception will be raised if max_results (or more) locations are
    returned in any given radius search, as this indicates some locations have
    been truncated. If this occurs, more granular searchable points files need
    to be supplied, and search_raidus needs to be selected carefully to ensure
    that max_results (or more) locations are never returned for any radius
    search.

    If clean ups or additional field extraction is required from the source
    data, override the parse_item function. Two parameters are passed:
      item: an ATP "Feature" class
      location: a dictionary which is returned from the store locator JSON
                response for a particular location.
    """

    allowed_domains: list[str] = []
    start_urls: list[str] = []
    days: dict | None = None
    iseadgg_countries_list: list[str] = []
    searchable_points_files: list[str] = []
    area_field_filter: list[str] = []
    search_radius: int = 0
    max_results: int = 0
    possible_days: list[dict] = DAYS_BY_FREQUENCY

    async def start(self) -> AsyncIterator[JsonRequest]:
        if len(self.iseadgg_countries_list) > 0 and self.search_radius != 0 and self.max_results != 0:
            for request in self.start_requests_geo_search_iseadgg_method():
                yield request
        elif len(self.searchable_points_files) > 0 and self.search_radius != 0 and self.max_results != 0:
            for request in self.start_requests_geo_search_manual_method():
                yield request
        else:
            for request in self.start_requests_all_at_once_method():
                yield request

    def start_requests_all_at_once_method(self) -> Iterable[JsonRequest]:
        """
        PREFERRED all-results-at-once method requiring only a
        single API call to the API endpoint. May be disabled
        by some API endpoints, requiring the NONPREFERRED
        geographic radius search method to be used instead.
        """
        if len(self.start_urls) == 0 and len(self.allowed_domains) == 1:
            yield JsonRequest(
                url=f"https://{self.allowed_domains[0]}/wp-admin/admin-ajax.php?action=store_search&autoload=1"
            )
        elif len(self.start_urls) == 1:
            yield JsonRequest(url=self.start_urls[0])
        else:
            raise ValueError(
                "Specify one domain name in the allowed_domains list attribute or one URL in the start_urls list attribute."
            )

    def start_requests_geo_search_iseadgg_method(self) -> Iterable[JsonRequest]:
        """
        NONPREFERRED geographic radius search method with
        PREFERRED ISEADGG method of specifying centroids.
        """
        if self.max_results == 0 or self.search_radius == 0:
            raise ValueError(
                "The max_results and search_radius attributes must be specified to each be more than 0 if iseadgg_countries_list is specified."
            )
            return
        if self.search_radius >= 458:
            iseadgg_radius = 458
        elif self.search_radius >= 315:
            iseadgg_radius = 315
        elif self.search_radius >= 158:
            iseadgg_radius = 158
        elif self.search_radius >= 94:
            iseadgg_radius = 94
        elif self.search_radius >= 79:
            iseadgg_radius = 79
        elif self.search_radius >= 48:
            iseadgg_radius = 48
        elif self.search_radius >= 24:
            iseadgg_radius = 24
        else:
            raise ValueError(
                "A minimum search_radius of 24 (kilometres) is required to be used for the ISEADGG geographic radius search method."
            )
        for lat, lon in country_iseadgg_centroids(self.iseadgg_countries_list, iseadgg_radius):
            if len(self.start_urls) == 0 and len(self.allowed_domains) == 1:
                yield JsonRequest(
                    url=f"https://{self.allowed_domains[0]}/wp-admin/admin-ajax.php?action=store_search&lat={lat}&lng={lon}&max_results={self.max_results}&search_radius={self.search_radius}"
                )
            elif len(self.start_urls) == 1:
                yield JsonRequest(
                    url=f"{self.start_urls[0]}&lat={lat}&lng={lon}&max_results={self.max_results}&search_radius={self.search_radius}"
                )
            else:
                raise ValueError(
                    "Specify one domain name in the allowed_domains list attribute or one URL in the start_urls list attribute."
                )

    def start_requests_geo_search_manual_method(self) -> Iterable[JsonRequest]:
        """
        NONPREFERRED geographic radius search method with
        NONPREFERRED searchable_points_file method of
        specifying centroids.
        """
        if self.max_results == 0 or self.search_radius == 0:
            raise ValueError(
                "The max_results and search_radius attributes must be specified to each be more than 0 if searchable_points_file is specified."
            )
            return
        for searchable_points_file in self.searchable_points_files:
            for lat, lon in point_locations(searchable_points_file, self.area_field_filter):
                if len(self.start_urls) == 0 and len(self.allowed_domains) == 1:
                    yield JsonRequest(
                        url=f"https://{self.allowed_domains[0]}/wp-admin/admin-ajax.php?action=store_search&lat={lat}&lng={lon}&max_results={self.max_results}&search_radius={self.search_radius}"
                    )
                elif len(self.start_urls) == 1:
                    yield JsonRequest(
                        url=f"{self.start_urls[0]}&lat={lat}&lng={lon}&max_results={self.max_results}&search_radius={self.search_radius}"
                    )
                else:
                    raise ValueError(
                        "Specify one domain name in the allowed_domains list attribute or one URL in the start_urls list attribute."
                    )

    def parse(self, response: TextResponse) -> Iterable[Feature]:
        if response.text.strip():
            features = response.json()
        else:
            # Empty pages are sometimes returned when there are no features
            # nearby a specified WGS84 coordinate.
            features = []

        if self.max_results > 0:
            if self.crawler.stats:
                if len(features) > 0:
                    self.crawler.stats.inc_value("atp/geo_search/hits")
                else:
                    self.crawler.stats.inc_value("atp/geo_search/misses")
                self.crawler.stats.max_value("atp/geo_search/max_features_returned", len(features))

            if len(features) >= self.max_results:
                self.logger.error(
                    "Locations have probably been truncated due to max_results (or more) features being returned by a single geographic radius search. Use a smaller search_radius."
                )

        for feature in features:
            self.pre_process_data(feature)
            item = DictParser.parse(feature)
            item.pop("addr_full", None)
            item["street_address"] = merge_address_lines([feature.get("address"), feature.get("address2")])
            item["name"] = html.unescape(feature["store"])

            if self.days is not None:
                # If we have preconfigured the exact days to use, start there
                item["opening_hours"] = self.parse_opening_hours(feature, self.days)
            elif DictParser.get_first_key(feature, DictParser.hours_keys):
                # Otherwise, iterate over the possibilities until we get a first match
                self.logger.warning(
                    "Attempting to detect opening hours - specify self.days = DAYS_EN or the appropriate language code to suppress this warning"
                )
                for days in self.possible_days:
                    item["opening_hours"] = self.parse_opening_hours(feature, days)
                    if item["opening_hours"] is not None:
                        self.days = days
                        break

            yield from self.post_process_item(item, response, feature) or []

    def parse_opening_hours(self, feature: dict, days: dict) -> OpeningHours:
        oh = OpeningHours()
        hours_raw = DictParser.get_first_key(feature, DictParser.hours_keys)
        if hours_raw:
            hours_raw = " ".join(filter(None, map(str.strip, Selector(text=hours_raw).xpath("//text()").getall())))
            oh.add_ranges_from_string(hours_raw, days=days)
        return oh

    def pre_process_data(self, feature: dict) -> None:
        """Override with any pre-processing on the item."""

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        """Override with any post-processing on the item."""
        yield item
