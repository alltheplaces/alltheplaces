from typing import AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.geo import country_iseadgg_centroids
from locations.items import Feature


class IpirangaBRSpider(Spider):
    name = "ipiranga_br"
    item_attributes = {"brand": "Ipiranga", "brand_wikidata": "Q2081136"}

    async def start(self) -> AsyncIterator[JsonRequest]:
        for lat, lon in country_iseadgg_centroids("BR", 158):
            yield JsonRequest(
                f"https://localizador.ipiranga.com.br/find-posto?filtroDistancia=160&posLat={lat}&posLong={lon}"
            )

    def parse(self, response):
        for station in response.json():
            if station.get("removido"):
                continue
            item = Feature()
            item["ref"] = station["id"]
            item["name"] = station.get("nome")
            item["street_address"] = station.get("rua")
            item["city"] = station.get("cidade")
            item["state"] = station.get("estado")
            item["postcode"] = station.get("cep")
            neighborhood = station.get("bairro")
            if neighborhood:
                item["extras"]["addr:suburb"] = neighborhood
            item["phone"] = station.get("telefoneFormated")
            item["lat"] = station.get("latitude")
            item["lon"] = station.get("longitude")
            item["website"] = "https://www.ipiranga.com.br"
            apply_category(Categories.FUEL_STATION, item)
            yield item
