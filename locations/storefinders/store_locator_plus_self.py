from scrapy import Spider
from scrapy.http import FormRequest

from locations.dict_parser import DictParser
from locations.geo import country_iseadgg_centroids, point_locations

# This store finder is a self-hosted WordPress plugin with a website
# of https://wordpress.org/plugins/store-locator-le/ and source code
# at https://github.com/wp-plugins/store-locator-le
#
# This store finder is not to be confused with the
# software-as-a-service store locator of the same name, from the
# same company, that is documented at https://storelocatorplus.com/
#
# To use this spider, specify a value for allowed_domains and the
# default path for the StoreLocatorPlus API endpoint will be used.
# In the event the default path is different, you can alternatively
# specify a value for start_url. Then specify either:
#
# PREFERRED
# 1. A list of ISO-3166 alpha-2 country codes as the
#    iseadgg_countries_list parameter and a suitable non-zero
#    search_radius value in kilometres.
#
#    Example:
#      iseadgg_countries_list = ["US", "CA"]
#      search_radius = 100
#
#      In this example, a 94km ISEADGG centroid grid will
#      automatically be selected as the most appropriate to use
#      against a 100km search radius accepted by the API endpoint.
#
# NONPREFERRED
# 2. A list of searchable_points_files = [x, y..] suitable for use
#    with the point_locations function of locations.geo and a
#    suitable non-zero search_radius value in kilometres.
#
# A non-zero value is also required for the max_results attribute.
# This number is set by the server and cannot be changed. To obtain
# this max_results value, observe an API call and check the JSON
# response:  data_queries["standard_location_load"]["query"] to
# obtain the number from the SQL LIMIT clause.
#
# An exception will be raised if max_results (or more) locations
# are returned in any given radius search, as this indicates some
# locations have been truncated. If this occurs, search_radius
# needs to be reduced to ensure that max_results (or more) locations
# are never returned for any radius search.
#
# If clean ups or additional field extraction is required from the
# source data, override the parse_item function. Two parameters are
# passed, item (and ATP "Feature" class) and location (a dict which
# is returned from the store locator JSON response for a particular
# location).


class StoreLocatorPlusSelfSpider(Spider):
    iseadgg_countries_list: list[str] = []
    searchable_points_files: list[str] = []
    search_radius: int = 0
    max_results: int = 0

    def start_requests(self):
        if hasattr(self, "allowed_domains"):
            url = f"https://{self.allowed_domains[0]}/wp-admin/admin-ajax.php"
        else:
            url = self.start_urls[0]
        if url and len(self.iseadgg_countries_list) > 0 and self.search_radius != 0 and self.max_results != 0:
            # PREFERRED geographic radius search method using ISEADGG
            # centroids for a supplied list of ISO-3166 alpha-2 country codes.
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
                raise RuntimeError(
                    "A minimum search_radius of 24 (kilometres) is required to be used for the ISEADGG geographic radius search method."
                )
            for lat, lon in country_iseadgg_centroids(self.iseadgg_countries_list, iseadgg_radius):
                formdata = {
                    "action": "csl_ajax_onload",
                    "lat": str(lat),
                    "lng": str(lon),
                    "radius": str(self.search_radius),
                }
                yield FormRequest(url=url, formdata=formdata, method="POST")
        elif url and len(self.searchable_points_files) > 0 and self.search_radius != 0 and self.max_results != 0:
            # NONPREFERRED geographic radius search method using a manually
            # specified list of searchable_points_file containing centroids.
            for searchable_points_file in self.searchable_points_files:
                for lat, lon in point_locations(searchable_points_file):
                    formdata = {
                        "action": "csl_ajax_onload",
                        "lat": str(lat),
                        "lng": str(lon),
                        "radius": str(self.search_radius),
                    }
                    yield FormRequest(url=url, formdata=formdata, method="POST")

    def parse(self, response, **kwargs):
        locations = response.json()["response"]

        if self.max_results > 0:
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
            item = DictParser.parse(location)
            item.pop("addr_full", None)
            item["street_address"] = ", ".join(filter(None, [location.get("address"), location.get("address2")]))
            if item["website"] and item["website"].startswith("/") and hasattr(self, "allowed_domains"):
                item["website"] = f"https://{self.allowed_domains[0]}{item['website']}"
            yield from self.parse_item(item, location) or []

    def parse_item(self, item, location, **kwargs):
        yield item
