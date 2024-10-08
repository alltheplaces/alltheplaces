from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser

# To use this spider, specify api_brand_name as the brand name key existing
# in calls to the Easy Locator API at https://easylocator.net/ajax/...
#
# Example source URL: https://easylocator.net/ajax/search_by_lat_lon_geojson/gigiscupcakesusa/-37.86/144.9717/0/10/null/null
# Example api_brand_name from source URL: gigiscupcakesusa


class EasyLocatorSpider(Spider):
    dataset_attributes = {"source": "api", "api": "easylocator.net"}
    api_brand_name: str = None

    def start_requests(self):
        yield JsonRequest(
            url=f"https://easylocator.net/ajax/search_by_lat_lon_geojson/{self.api_brand_name}/0/0/0/null/null/null"
        )

    def parse(self, response):
        for location in response.json()["physical"]:
            item = DictParser.parse(location["properties"])
            item["postcode"] = location["properties"]["zip_postal_code"]
            yield from self.parse_item(item, location) or []

    def parse_item(self, item, location):
        yield item
