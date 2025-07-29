import scrapy

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class JetDESpider(scrapy.Spider):
    name = "jet_de"
    item_attributes = {"brand": "JET", "brand_wikidata": "Q568940"}
    start_urls = [
        "https://www.jet.de/api/v1/stations_within_bounds?n=85.0511287798066&e=180&s=-67.90083807146054&w=-180&withCardHtml=1"
    ]

    def parse(self, response, **kwargs):
        for station in response.json()["stations"]:
            item = DictParser.parse(station)
            item["ref"] = station["publicId"]
            item["website"] = station["webUrl"]
            apply_category(Categories.FUEL_STATION, item)
            yield item
