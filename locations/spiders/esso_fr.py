from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.geo import points


class EssoSpider(Spider):
    name = "esso_fr"
    item_attributes = {
        "brand": "Esso",
        "brand_wikidata": "Q867662",
    }
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def start_requests(self):
        for lat, lng in points(grid_size=40, a2_country_codes=["FR"]):
            fr_url = f"https://carburant.esso.fr/api/RetailLocator/GetRetailLocations?DataSource=RetailGasStations&country=FR&Latitude1={lat-0.5}&Longitude1={lng-1}&Latitude2={lat+0.5}&Longitude2={lng+1}"
            market_request = JsonRequest(url=fr_url, method="GET")
            yield market_request

    def parse(self, response):
        locations = response.json().get("Locations")
        for location in locations:
            p = DictParser().parse(location)
            p["ref"] = location.get("LocationID")
            yield p
