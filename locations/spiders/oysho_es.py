import scrapy

from locations.dict_parser import DictParser
from locations.user_agents import BROSWER_DEFAULT
from locations.geo import point_locations


class OyshoSpider(scrapy.Spider):
    name = "oysho"
    item_attributes = {
        "brand": "Oysho",
        "brand_wikidata": "Q3327046",
    }
    allowed_domains = ["oysho.com"]
    user_agent = BROSWER_DEFAULT

    def start_requests(self):
        for lat, lon in point_locations("eu_centroids_120km_radius_country.csv", "ES"):
            url = "https://www.oysho.com/itxrest/2/bam/store/64009600/physical-store?languageId=-1&appId=1&latitude={}&longitude={}&countryCode=ES&radioMax=5000"
            yield scrapy.Request(url=url.format(lat, lon))

    def parse(self, response):
        for data in response.json().get("closerStores"):
            item = DictParser.parse(data)

            yield item
