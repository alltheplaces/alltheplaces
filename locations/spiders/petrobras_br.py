from typing import Any, AsyncIterator

from scrapy import FormRequest, Spider
from scrapy.http import Response

from locations.categories import Categories, Fuel, apply_category, apply_yes_no
from locations.items import Feature

FUEL_MAP = {
    "gasNatural": Fuel.CNG,
    "gasolinaPodium": Fuel.OCTANE_102,
    "gasolinaGrid": Fuel.GASOLINE,
    "dieselS10": Fuel.DIESEL,
    "dieselPodium": Fuel.DIESEL,
    "dieselGrid": Fuel.DIESEL,
    "etanolHidratado": Fuel.ETHANOL,
    "etanolHidratadoGrid": Fuel.ETHANOL,
    "etanolGrid": Fuel.ETHANOL,
    "lubrax": Fuel.ENGINE_OIL,
    "fluaPetrobras": Fuel.ADBLUE,
}

STATES_BR = {
    "Acre": "AC",
    "Alagoas": "AL",
    "Amapa": "AP",
    "Amazonas": "AM",
    "Bahia": "BA",
    "Ceara": "CE",
    "Distrito Federal": "DF",
    "Espirito Santo": "ES",
    "Goias": "GO",
    "Maranhao": "MA",
    "Mato Grosso": "MT",
    "Mato Grosso do Sul": "MS",
    "Minas Gerais": "MG",
    "Para": "PA",
    "Paraiba": "PB",
    "Parana": "PR",
    "Pernambuco": "PE",
    "Piaui": "PI",
    "Rio Grande do Norte": "RN",
    "Rio Grande do Sul": "RS",
    "Rio de Janeiro": "RJ",
    "Rondonia": "RO",
    "Roraima": "RR",
    "Santa Catarina": "SC",
    "Sao Paulo": "SP",
    "Sergipe": "SE",
    "Tocantins": "TO",
}


class PetrobrasBRSpider(Spider):
    name = "petrobras_br"
    item_attributes = {"brand": "BR", "brand_wikidata": "Q4836468"}

    async def start(self) -> AsyncIterator[Any]:
        base_url = "https://www.postospetrobras.com.br/api/get_postos"
        for state in STATES_BR.values():
            yield FormRequest(
                url=base_url,
                formdata={"estado": state, "cidade": ""},
            )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for data in response.json():
            item = Feature()
            item["ref"] = data["codigoSAP"]
            item["name"] = data["nome"]
            item["street_address"] = data["logradouro"]
            item["postcode"] = data["cep"]
            item["state"] = data["estado"]
            item["city"] = data["cidade"]
            neighborhood = data.get("bairro")
            if neighborhood:
                item["extras"]["addr:suburb"] = neighborhood
            item["phone"] = data.get("telefone")
            lat = data.get("latitude")
            lon = data.get("longitude")
            if lat and lon:
                item["lat"] = lat
                item["lon"] = lon
            for field, tag in FUEL_MAP.items():
                apply_yes_no(tag, item, data.get(field, False))
            apply_category(Categories.FUEL_STATION, item)
            yield item
