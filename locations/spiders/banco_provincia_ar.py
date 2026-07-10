from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class BancoProvinciaARSpider(Spider):
    name = "banco_provincia_ar"
    item_attributes = {"brand": "Banco Provincia", "brand_wikidata": "Q4856209"}

    async def start(self) -> AsyncIterator[JsonRequest]:
        # Bulk endpoints published by the branch finder's appsettings.json. "filiales" is intentionally
        # skipped: its entries are correspondent banks in other countries and two coordinate-less foreign
        # offices (Montevideo, São Paulo) — none of them Argentine Banco Provincia locations.
        for location_type, endpoint in (("branch", "sucursales"), ("atm", "cajeros")):
            yield JsonRequest(
                url="https://www.bancoprovincia.com.ar/gateway/webback/buscador/{}".format(endpoint),
                cb_kwargs={"location_type": location_type},
            )

    def parse(self, response: Response, location_type: str, **kwargs: Any) -> Any:
        for location in response.json():
            item = DictParser.parse(location)
            item["city"] = location.get("localidad")
            item["state"] = location.get("provincia")  # CABA or Buenos Aires province
            item["postcode"] = location.get("codigoPostal")

            if location_type == "branch":
                item["ref"] = str(location["numero"])
                item["branch"] = item.pop("name", None)  # DictParser maps "nombre" -> name
                item["street_address"] = location["domicilio"]
                item.pop("phone", None)  # "telefono" is a doubled, multi-number string, not a clean phone
                # "horario" carries only a time range with no weekdays ("10 a 15 hs"), so no opening_hours.
                apply_category(Categories.BANK, item)
            else:
                # ATMs have no id of their own; idSucursal + street uniquely identifies each machine.
                item["ref"] = "{}-{}".format(location["idSucursal"], location["direccion"])
                item["street_address"] = item.pop("addr_full", None)  # DictParser maps "direccion"
                apply_category(Categories.ATM, item)

            yield item
