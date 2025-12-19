from typing import AsyncIterator

import xmltodict
from scrapy import Spider
from scrapy.http import Request

from locations.categories import Categories, apply_category
from locations.geo import point_locations
from locations.items import Feature


class BancoSabadellESSpider(Spider):
    name = "banco_sabadell_es"
    item_attributes = {"brand": "Banco Sabadell", "brand_wikidata": "Q762330"}

    async def start(self) -> AsyncIterator[Request]:
        for lat, lon in point_locations("eu_centroids_120km_radius_country.csv", "ES"):
            for type in ["oficinas", "cajeros"]:
                yield Request(
                    f"https://www.bancsabadell.com/cs/Satellite?pagename=GrupoBS/GBS_Gmaps/servicioGMaps&long={lon}&lat={lat}&{type}=true",
                    cb_kwargs={"type": type},
                )

    def parse(self, response, **kwargs):
        for data in xmltodict.parse(response.body)["provincias"]["oficina"]:
            item = Feature()
            item["ref"] = " - ".join([data["@numero"], kwargs["type"]])
            item["branch"] = data["@nombre"]
            item["street"] = data["@direccion"]
            item["phone"] = data["@telefono"]
            item["addr_full"] = data["@address"]
            item["lat"] = data["@lat"]
            item["lon"] = data["@lng"]
            item["country"] = data["@pais"]
            if kwargs["type"] == "oficinas":
                apply_category(Categories.BANK, item)
            else:
                apply_category(Categories.ATM, item)
            yield item
