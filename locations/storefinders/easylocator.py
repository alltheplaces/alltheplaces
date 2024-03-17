from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.geo import point_locations


# To use this spider, either specify the start_urls or
# pass in a coordinates file.
#
# Example: https://easylocator.net/ajax/search_by_lat_lon_geojson/gigiscupcakesusa/-37.86/144.9717/0/10/null/null
class EasyLocatorSpider(Spider):
    dataset_attributes = {"source": "api", "api": "easylocator.net"}
    allowed_domains = ["easylocator.net"]
    searchable_points_files = []
    search_radius = 0
    max_results = 1000

    def start_requests(self):
        if len(self.start_urls) != 0:
            for url in self.start_urls:
                if len(self.searchable_points_files) > 0 and self.search_radius != 0 and self.max_results != 0:
                    for searchable_points_file in self.searchable_points_files:
                        for lat, lon in point_locations(searchable_points_file):
                            yield JsonRequest(
                                url=f"{url}/{self.api_key}/{lat}/{lon}/{self.search_radius}/{self.max_results}/null/null"
                            )
                else:
                    yield JsonRequest(url=url)

    def parse(self, response):
        for location in response.json()["physical"]:
            item = DictParser.parse(location["properties"])
            item["postcode"] = location["properties"]["zip_postal_code"]
            yield from self.parse_item(item, location) or []

    def parse_item(self, item, location):
        yield item
