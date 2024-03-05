from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class RepsolPESpider(Spider):
    name = "repsol_pe"
    item_attributes = {"brand": "Repsol", "brand_wikidata": "Q174747"}
    allowed_domains = ["www.repsol.pe"]
    start_urls = [
        "https://www.repsol.pe/content/dam/aplicaciones/repsol-paises/pe/es/estaciones-de-servicio/data/data.json"
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
            apply_category(Categories.FUEL_STATION, item)
            yield item
