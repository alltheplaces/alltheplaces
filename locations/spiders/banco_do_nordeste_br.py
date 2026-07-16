from typing import Any, Iterable

import scrapy
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_WEEKDAY, OpeningHours
from locations.items import Feature


class BancoDoNordesteBRSpider(scrapy.Spider):
    name = "banco_do_nordeste_br"
    item_attributes = {"brand": "Banco do Nordeste", "brand_wikidata": "Q4854137"}
    start_urls = ["https://api.bnb.gov.br/corporativo/api/agencia/endereco?codigoMunicipio=&siglaUf=&tamanho=10000"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        for location in response.json():
            item = Feature()
            item["branch"] = location["descricao"]
            item["street"] = location["logradouro"]
            item["housenumber"] = str(location["numero"]) if location.get("numero") else None
            item["state"] = location["siglaUf"]
            item["city"] = location["nomeMunicipio"]
            item["postcode"] = str(location["cep"])
            item["ref"] = location["codigo"]

            if (ddd := location.get("numeroDDD")) and (number := location.get("numeroTelefone")):
                item["phone"] = f"+55 {ddd.lstrip('0')} {number}"

            opening = location.get("horarioAbertura")
            closing = location.get("horarioFechamento")
            if opening and closing and opening != "00:00" and closing != "00:00":
                item["opening_hours"] = OpeningHours()
                item["opening_hours"].add_days_range(DAYS_WEEKDAY, opening, closing)

            apply_category(Categories.BANK, item)
            yield item
