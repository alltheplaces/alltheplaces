from typing import Any

import scrapy
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature


class BancoDoNordesteBRSpider(scrapy.Spider):
    name = "banco_do_nordeste_br"
    item_attributes = {"brand": "Banco do Nordeste", "brand_wikidata": "Q4854137"}
    start_urls = ["https://api.bnb.gov.br/corporativo/api/agencia/endereco?codigoMunicipio=&siglaUf=&tamanho=10000"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json():
            item = Feature()
            item["branch"] = location["descricao"]
            item["street"] = location["logradouro"]
            item["housenumber"] = location["numero"]
            item["state"] = location["siglaUf"]
            item["city"] = location["nomeMunicipio"]
            item["postcode"] = str(location["cep"])
            item["ref"] = location["codigo"]
            apply_category(Categories.BANK, item)
            yield item
