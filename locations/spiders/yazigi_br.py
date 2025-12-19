import scrapy

from locations.categories import apply_category
from locations.dict_parser import DictParser


class YazigiBRSpider(scrapy.Spider):
    name = "yazigi_br"
    item_attributes = {"brand": "Yázigi", "brand_wikidata": "Q10394813"}

    def start_requests(self):
        url = "https://www.yazigi.com.br/BuscaUnidadesMapa"
        yield scrapy.FormRequest(
            url=url,
            formdata={"isLead": "false", "isMapa": "true", "isTeste": "false"},
        )

    def parse(self, response, **kwargs):
        data = response.json()["Unidades"]
        for poi in data:
            poi["Unidade"].update(poi["Unidade"].pop("Coordenadas"))
            item = DictParser.parse(poi["Unidade"])
            item["ref"] = poi["Unidade"].get("CodigoEmitente")
            item["branch"] = poi["Unidade"].get("NomeFantasia")
            item["phone"] = poi["Unidade"].get("Telefone")
            address = poi["Unidade"]["Endereco"]
            item["addr_full"] = address.get("Logradouro")
            item["city"] = address.get("CidadeNome")
            item["state"] = address.get("EstadoNome")
            item["postcode"] = address.get("CEP")
            apply_category({"amenity": "language_school"}, item)

            yield item
