from scrapy import Spider

from locations.dict_parser import DictParser


class SonicCASpider(Spider):
    name = "sonic_ca"
    item_attributes = {"brand": "Sonic", "brand_wikidata": "Q118669677"}
    start_urls = ["https://energiesonic.com/wp-json/wpgmza/v1/features"]

    def parse(self, response, **kwargs):
        for location in response.json()["markers"]:
            yield DictParser.parse(location)
