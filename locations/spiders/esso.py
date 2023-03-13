from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser


class EssoSpider(Spider):
    name = "esso"
    item_attributes = {
        "brand": "Esso",
        "brand_wikidata": "Q867662",
    }
    custom_settings = {"ROBOTSTXT_OBEY": False}
    fr_url = "https://carburant.esso.fr/api/RetailLocator/GetRetailLocations?DataSource=RetailGasStations"
    uk_url = "https://www.esso.co.uk/api/RetailLocator/GetRetailLocations?DataSource=RetailGasStations"
    urls = [fr_url, uk_url]

    def start_requests(self):
        for url in self.urls:
            market_request = JsonRequest(url=url, method="GET")
            yield market_request

    def parse(self, response):
        locations = response.json().get("Locations")
        for location in locations:
            p = DictParser().parse(location)
            p["ref"] = location.get("LocationID")
            yield p
