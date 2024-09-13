from typing import Any, Iterable

from scrapy import FormRequest, Spider
from scrapy.http import Response

from locations.categories import apply_category
from locations.items import Feature


class SosBRSpider(Spider):
    name = "sos_br"
    item_attributes = {"brand": "SOS Technologia e Educação", "brand_wikidata": "Q129847471"}
    requires_proxy = True

    def start_requests(self) -> Iterable[FormRequest]:
        yield FormRequest(
            url="https://www.sos.com.br/BuscaUnidadesMapa",
            method="POST",
            formdata={"isLead": "false", "isMapa": "true", "isTeste": "false"},
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["Unidades"]:
            item = Feature()
            item["extras"]["sources"] = [location]
            item["ref"] = location["ID"]
            item["name"] = location["NomeFantasia"]
            item["phone"] = location["Telefone"]
            item["email"] = location["Email"]
            item["street"] = location["Endereco"]["Logradouro"]
            item["housenumber"] = location["Endereco"]["Numero"]
            item["city"] = location["Endereco"]["CidadeNome"]
            item["extras"]["addr:district"] = location["Endereco"]["Bairro"]
            item["state"] = location["Endereco"]["EstadoNome"]
            item["lat"] = location["Coordenadas"]["Latitude"]
            item["lon"] = location["Coordenadas"]["Longitude"]
            apply_category({"office": "business"}, item)

            yield item
