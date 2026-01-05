from typing import AsyncIterator

from scrapy import Spider
from scrapy.http import Request

from locations.categories import Categories, apply_category
from locations.geo import city_locations
from locations.items import Feature


class BankinterESSpider(Spider):
    name = "bankinter_es"
    item_attributes = {"brand": "Bankinter", "brand_wikidata": "Q806808"}

    async def start(self) -> AsyncIterator[Request]:
        for city in city_locations("ES", 40000):
            # BANK URL
            yield Request(
                url="https://bancaonline.bankinter.com/publico/rs/loc/oficinas?lat={}&lng={}&max=11&tipo=OF".format(
                    city["latitude"], city["longitude"]
                ),
                callback=self.branch_data,
            )
            # ATM URL
            yield Request(
                url="https://bancaonline.bankinter.com/publico/rs/loc/cajeros?lat={}&lng={}&max=11&tipo=Bankinter&time=1669031848635".format(
                    city["latitude"], city["longitude"]
                ),
                method="POST",
                callback=self.atm_data,
            )

    def branch_data(self, response):
        for data in response.json()["list"]:
            data_addr = data["centrosBean"]
            item = Feature()
            item["ref"] = data_addr["centro"]
            item["street_address"] = data_addr["direc1"]
            item["branch"] = data_addr["descrip"]
            item["city"] = data_addr["plaza"]
            item["postcode"] = data_addr["cpostal"]
            item["lat"] = data["centCordBean"]["coordY"]
            item["lon"] = data["centCordBean"]["coordX"]
            item["phone"] = data_addr["telefono1"]
            apply_category(Categories.BANK, item)
            yield item

    def atm_data(self, response):
        for data in response.json()["list"]:
            item = Feature()
            item["ref"] = data["nombreSucursal"]
            item["street_address"] = data["calle"]
            item["branch"] = data["nombreSucursal"]
            item["city"] = data["poblacion"]
            item["postcode"] = data["codigoPostal"]
            item["lat"] = data["latitud"]
            item["lon"] = data["longitud"]
            item["phone"] = data["telefono"]
            apply_category(Categories.ATM, item)
            yield item
