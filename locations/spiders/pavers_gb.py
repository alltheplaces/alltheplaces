
import scrapy
from scrapy import Spider

from locations.dict_parser import DictParser
from locations.geo import city_locations
from locations.items import Feature


class PaversGBSpider(Spider):
    name = "pavers_gb"
    item_attributes = {
        "brand": "Pavers",
        "brand_wikidata": "Q7155843",
        "country": "GB",
    }
    allowed_domains = ["pavers.co.uk"]

    def start_requests(self):
        url_template = "https://www.pavers.co.uk/api/storeLocation/search?query={city}&location={lat},{lon}&page=1"
        for city in city_locations("GB", 10000):
            yield scrapy.Request(url_template.format(city=city["name"], lat=city["latitude"], lon=city["longitude"]))

    def parse(self, response):
        for location in response.json()["result"]["response"]["results"]:
            item = Feature()
            item = DictParser.parse(location["data"])
            yield item
