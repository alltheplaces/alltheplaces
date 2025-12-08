from typing import AsyncIterator

from scrapy import Spider
from scrapy.http import Request

from locations.dict_parser import DictParser
from locations.geo import point_locations


class LongchampEUSpider(Spider):
    name = "longchamp_eu"
    item_attributes = {"brand": "Longchamp", "brand_wikidata": "Q1869471"}
    custom_settings = {"ROBOTSTXT_OBEY": False}

    async def start(self) -> AsyncIterator[Request]:
        template = "https://www.longchamp.com/on/demandware.store/Sites-Longchamp-EU-Site/de_DE/Stores-FindStores?showMap=true&radius=300&lat={}&lng={}"
        for lat, lon in point_locations("eu_centroids_120km_radius_country.csv"):
            yield Request(url=template.format(lat, lon))

    def parse(self, response):
        for store in response.json().get("stores"):
            item = DictParser.parse(store)

            yield item
