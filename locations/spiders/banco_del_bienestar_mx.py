import json
from typing import Any

from scrapy import FormRequest, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.google_url import url_to_coords
from locations.items import Feature


class BancoDelBienestarMXSpider(Spider):
    name = "banco_del_bienestar_mx"
    item_attributes = {
        "brand": "Banco del Bienestar",
        "brand_wikidata": "Q5719137",
    }
    start_urls = ["https://directoriodesucursales.bancodelbienestar.gob.mx"]
    token = ""
    requires_proxy = True

    def parse(self, response: Response, **kwargs: Any) -> Any:
        self.token = response.xpath('//input[@name="__RequestVerificationToken"]/@value').get()
        for state in json.loads(response.xpath('//input[@id="datosEntidad"]/@value').get()):
            yield FormRequest(
                url="https://directoriodesucursales.bancodelbienestar.gob.mx/Home/ListarMunalc",
                formdata={"idEnt": str(state["id_entidad"])},
                callback=self.parse_state,
                cb_kwargs={"state": state["descripcion"]},
            )

    def parse_state(self, response: Response, state: str) -> Any:
        for area in response.json()["response"]:
            yield FormRequest(
                url="https://directoriodesucursales.bancodelbienestar.gob.mx/Busqueda",
                formdata={
                    "entidad": str(area["idEnt"]),
                    "munalc": area["munalc"],
                    "__RequestVerificationToken": self.token,
                },
                callback=self.parse_locations,
                cb_kwargs={"state": state},
            )

    def parse_locations(self, response: Response, state: str) -> Any:
        if locations_data := response.xpath("//@data-sucursales").get():
            for location in json.loads(locations_data).get("response", []):
                item = Feature()
                item["state"] = state
                item["city"] = location["munalc"]
                item["ref"] = location["id"]
                item["branch"] = location["nomSuc"]
                item["addr_full"] = location["domicilio"]
                if map_url := location.get("liga"):
                    item["lat"], item["lon"] = url_to_coords(map_url)
                apply_category(Categories.BANK, item)
                yield item
