from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser


def valid_coordinates(latitude: str, longitude: str) -> tuple[float | None, float | None]:
    # Some records carry empty, "0", or transposed coordinates; keep only points inside Argentina.
    try:
        lat, lon = float(latitude.replace(",", ".")), float(longitude.replace(",", "."))
    except (AttributeError, ValueError):
        return None, None
    if -56.0 < lat < -21.0 and -74.0 < lon < -53.0:
        return lat, lon
    return None, None


class CredicoopARSpider(Spider):
    name = "credicoop_ar"
    item_attributes = {"brand": "Credicoop", "brand_wikidata": "Q4854086"}

    async def start(self) -> AsyncIterator[Any]:
        # {items_per_page}/{page}: one oversized page returns every record.
        yield JsonRequest(url="https://www.bancocredicoop.coop/api/filiales/Filiales/10000/1")
        yield JsonRequest(
            url="https://www.bancocredicoop.coop/api/cajeros/Cajeros/10000/1",
            callback=self.parse_atm,
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for branch in response.json()["filiales"]:
            item = DictParser.parse(branch)  # maps nombre (-> name), telefono (-> phone)
            item["ref"] = branch["id_filial"]
            item["branch"] = item.pop("name")
            item["street_address"] = branch["domicilio"]
            item["city"] = branch["localidad"]
            item["state"] = branch["provincia"]
            item["postcode"] = branch["codigo_postal"]
            item["lat"], item["lon"] = valid_coordinates(branch["latitud"], branch["longitud"])
            apply_yes_no(Extras.ATM, item, branch["cajero"] == "1")
            apply_category(Categories.BANK, item)
            yield item

    def parse_atm(self, response: Response, **kwargs: Any) -> Any:
        for atm in response.json()["cajeros"]:
            item = DictParser.parse(atm)  # maps direccion (-> addr_full)
            item["ref"] = atm["terminal"]
            item["street_address"] = item.pop("addr_full", None)
            item["city"] = atm["localidad"]
            item["state"] = atm["provincia"]
            item["lat"], item["lon"] = valid_coordinates(atm["latitud"], atm["longitud"])
            apply_category(Categories.ATM, item)
            yield item
