import scrapy

from locations.dict_parser import DictParser
from locations.geo import point_locations


class BirkenstockUsSpider(scrapy.Spider):
    name = "birkenstock_us"
    item_attributes = {
        "brand": "Dacia",
        "brand_wikidata": "Q648458",
    }
    allowed_domains = ["birkenstock.com"]

    def start_requests(self):
        point_files = "us_centroids_100mile_radius_state.csv"
        for lat, lon in point_locations(point_files):
            yield scrapy.Request(
                f"https://www.birkenstock.com/on/demandware.store/Sites-US-Site/en_US/Stores-GetStoresJson?latitude={lat}&longitude={lon}&&storeid=&distance=100&distanceunit=mi&searchText=&countryCode=US&storeLocatorType=regular",
            )

    def parse(self, response):
        for _, data in response.json().get("stores").items():
            yield DictParser.parse(data)
