from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class RepsolMXSpider(Spider):
    name = "repsol_mx"
    item_attributes = {"brand": "Repsol", "brand_wikidata": "Q174747"}
    allowed_domains = ["www.repsol.com.mx"]
    start_urls = [
        "https://www.repsol.com.mx/content/dam/aplicaciones/repsol-paises/mx/es/estaciones-de-servicio/data/data.json"
    ]

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response):
        for location in response.json():
            item = DictParser.parse(location)
            # The latitude and longitude values in the JSON are flipped
            item["lat"], item["lon"] = item["lon"], item["lat"]
            item["ref"] = location["subTitle"].split(" - ", 1)[0]
            item["street_address"] = item.pop("addr_full", None)
            item["postcode"] = location["cp"]
            item.pop("website", None)
            apply_category(Categories.FUEL_STATION, item)
            yield item
