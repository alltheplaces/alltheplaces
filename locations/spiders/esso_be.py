from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.geo import points
from locations.items import Feature


class EssoSpider(Spider):
    name = "esso_be"
    item_attributes = {
        "brand": "Esso",
        "brand_wikidata": "Q867662",
    }
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def start_requests(self):
        for lat, lng in points(grid_size=5, a2_country_codes=["BE"]):
            print(lat, lng)
            be_url = f"https://www.esso.be/fr-be/api/RetailLocator/GetRetailLocations?DataSource=RetailGasStations&country=BE&Latitude1={lat-0.5}&Longitude1={lng-1}&Latitude2={lat+0.5}&Longitude2={lng+1}"
            market_request = JsonRequest(url=be_url, method="GET")
            yield market_request

    def parse(self, response):
        locations = response.json().get("Locations")
        print("parsing", response.json())
        for location in locations:
            print(location.get("LocationID"))
            p = DictParser().parse(location)
            p["ref"] = location.get("LocationID")
            yield p
