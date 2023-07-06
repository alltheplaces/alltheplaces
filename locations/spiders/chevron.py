import scrapy

from locations.dict_parser import DictParser
from locations.geo import point_locations


class ChevronSpider(scrapy.Spider):
    name = "chevron"
    item_attributes = {"brand": "Chevron", "brand_wikidata": "Q319642"}

    def start_requests(self):
        url = "https://apis.chevron.com/api/StationFinder/nearby?clientid=A67B7471&lat={}&lng={}&brand=chevronTexaco&radius=35"
        for lat, lon in point_locations("us_centroids_25mile_radius_state.csv"):
            yield scrapy.Request(url.format(lat, lon), callback=self.parse)

    def parse(self, response):
        for data in response.json().get("stations"):
            yield DictParser.parse(data)
