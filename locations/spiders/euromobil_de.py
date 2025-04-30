import scrapy

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class EuromobilDESpider(scrapy.Spider):
    name = "euromobil_de"
    item_attributes = {
        "brand": "Euromobil",
        "brand_wikidata": "Q1375118",
    }
    start_urls = ["https://euromobil.de/rest/search_emstations/50.1109221/8.6821267/10000/"]

    def parse(self, response, **kwargs):
        for station in response.json():
            item = DictParser.parse(station)
            item["street_address"] = item.pop("street")
            item["ref"] = station["stationid"]
            apply_category(Categories.CAR_RENTAL, item)
            yield item
