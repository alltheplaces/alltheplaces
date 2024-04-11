from scrapy import Spider
from scrapy.http import FormRequest

from locations.dict_parser import DictParser
from locations.geo import point_locations

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
# specify a value for start_url. Then add one or more searchable
# points files as searchable_points_files = [x, y..] and also
# specify a non-zero number for search_radius = x. A non-zero number
# is also required for the max_results attribute. This number is set
# by the server and cannot be changed. To obtain this max_results
# number, observe an API call and check the JSON response:
# data_queries["standard_location_load"]["query"] to obtain the
# number from the SQL LIMIT clause.
#
# An exception will be raised if max_results (or more) locations
# are returned in any given radius search, as this indicates some
# locations have been truncated. If this occurs, more granular
# searchable points files need to be supplied, and search_radius
# needs to be selected carefully to ensure that max_results (or
# more) locations are never returned for any radius search.
#
# If clean ups or additional field extraction is required from the
# source data, override the parse_item function. Two parameters are
# passed, item (and ATP "Feature" class) and location (a dict which
# is returned from the store locator JSON response for a particular
# location).


class StoreLocatorPlusSelfSpider(Spider):
    searchable_points_files = []
    search_radius = 0
    max_results = 0

    def start_requests(self):
        if hasattr(self, "allowed_domains"):
            url = f"https://{self.allowed_domains[0]}/wp-admin/admin-ajax.php"
        else:
            url = self.start_urls[0]
        if url and len(self.searchable_points_files) > 0 and self.search_radius != 0 and self.max_results != 0:
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
        if len(response.json()["response"]) >= self.max_results and self.max_results > 0:
            raise RuntimeError(
                "Locations have probably been truncated due to max_results (or more) locations being returned by a single geographic radius search. Use more granular searchable_points_files and a smaller search_radius."
            )
        for location in response.json()["response"]:
            # print(location)
            item = DictParser.parse(location)
            item.pop("addr_full", None)
            item["street_address"] = ", ".join(filter(None, [location.get("address"), location.get("address2")]))
            if item["website"] and item["website"].startswith("/") and hasattr(self, "allowed_domains"):
                item["website"] = f"https://{self.allowed_domains[0]}{item['website']}"
            yield from self.parse_item(item, location) or []

    def parse_item(self, item, location, **kwargs):
        yield item
