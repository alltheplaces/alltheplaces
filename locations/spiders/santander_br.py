from typing import Any

import chompjs
from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.geo import city_locations
from locations.items import Feature
from locations.user_agents import BROWSER_DEFAULT


class SantanderBRSpider(Spider):
    name = "santander_br"
    item_attributes = {"brand": "Banco Santander", "brand_wikidata": "Q2882087"}
    start_urls = ["https://www.santander.com.br/agencias"]
    user_agent = BROWSER_DEFAULT

    def parse(self, response: Response, **kwargs: Any) -> Any:
        app_key = chompjs.parse_js_object(
            response.xpath('//script[@type="text/javascript"][contains(text(),"appKey")]/text()').get()
        )["appKey"]
        for city in city_locations("BR", 15000):
            yield JsonRequest(
                url=f"https://esbapi.santander.com.br/institucional/v1/coordenates?gw-app-key={app_key}",
                data={"coordenada": {"latitude": city["latitude"], "longitude": city["longitude"]}, "local": "AMBOS"},
                callback=self.parse_locations,
            )

    def parse_locations(self, response: Response, **kwargs: Any) -> Any:
        if locations := response.json().get("agencias"):
            for location in locations:
                item = Feature()
                item["ref"] = location.get("codigo")
                description = location.get("descricao").title()
                item["name"] = "Santander Select" if "Select" in description else "Santander"
                item["lat"] = location["coordenada"].get("latitude")
                item["lon"] = location["coordenada"].get("longitude")
                item["housenumber"] = location.get("numero")
                item["street"] = location.get("logradouro")
                item["extras"]["addr:district"] = location.get("bairro")
                item["city"] = location.get("cidade")
                item["state"] = location.get("uf")
                item["postcode"] = location.get("cep")
                item["phone"] = location.get("telefone")
                apply_category(Categories.BANK, item)
                yield item
