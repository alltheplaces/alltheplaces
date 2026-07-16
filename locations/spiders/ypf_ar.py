from typing import Any, AsyncIterator

from scrapy import Request, Spider
from scrapy.http import Response

from locations.categories import Categories, Fuel, apply_category, apply_yes_no
from locations.dict_parser import DictParser


class YpfARSpider(Spider):
    name = "ypf_ar"
    item_attributes = {"brand": "YPF", "brand_wikidata": "Q2006989"}
    # mapa.ypf.com loads every service station from this endpoint. The YPF Full shop
    # (TIPO_FULL) is intentionally not tagged shop=convenience -- that top-level tag isn't
    # in YPF's amenity=fuel NSI entry and would break the match.

    async def start(self) -> AsyncIterator[Request]:
        # The endpoint returns "Acceso Denegado" unless the mapa.ypf.com referer is sent.
        yield Request(
            url="https://magui.ypf.com/boxes/eess/get/",
            headers={"Origin": "https://mapa.ypf.com", "Referer": "https://mapa.ypf.com/"},
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json():
            if location.get("ESTADO_DE_LA_BOCA") != "ACTIVA":
                continue  # inactive / closed station
            if location.get("TIPO_ESTABLECIMIENTO") == "PUNTO ELECTRICO":
                continue  # EV-only point, not a fuel station

            item = DictParser.parse(location)  # maps DIRECCION -> addr_full
            item["ref"] = str(location["APIES"])
            item["street_address"] = item.pop("addr_full", None)
            item["city"] = location.get("LOCALIDAD_GEOGRAFICA")
            item["state"] = location.get("PROVINCIA_GEOGRAFICA")
            item["postcode"] = location.get("CODIGO_POSTAL")
            item["lat"] = location.get("POINT_Y")
            item["lon"] = location.get("POINT_X")
            item["operator"] = location.get("RAZON_SOCIAL")

            apply_category(Categories.FUEL_STATION, item)
            apply_yes_no(Fuel.CNG, item, location.get("TIPO_DESPACHO") in ("DUAL", "GNC"))
            apply_yes_no(Fuel.ADBLUE, item, location.get("AZUL32") is True)  # "Azul 32" = AdBlue (AUS 32)
            apply_yes_no(Fuel.ELECTRIC, item, location.get("CARGADOR_ELECTRICO") == "SI")

            yield item
