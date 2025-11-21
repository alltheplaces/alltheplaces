from typing import AsyncIterator

from scrapy import Spider
from scrapy.http import Request

from locations.dict_parser import DictParser
from locations.geo import point_locations


class KiehlsDESpider(Spider):
    name = "kiehls_de"
    item_attributes = {
        "brand": "Kiehl's",
        "brand_wikidata": "Q3196447",
    }

    async def start(self) -> AsyncIterator[Request]:
        for lat, lon in point_locations("eu_centroids_20km_radius_country.csv", "DE"):
            url = "https://www.kiehls.de/on/demandware.store/Sites-kiehls-de-Site/de_DE/Stores-Search?lat={}&long={}&ajax=true"
            yield Request(url=url.format(lat, lon))

    def parse(self, response):
        for store in response.json()["storelocatorresults"]["stores"]:
            item = DictParser.parse(store)
            yield item
