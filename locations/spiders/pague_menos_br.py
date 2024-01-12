import json
from typing import Any

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.items import Feature
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS


class PagueMenosBRSpider(Spider):
    name = "pague_menos_br"
    item_attributes = {"brand": "Pague Menos", "brand_wikidata": "Q7124466"}
    start_urls = ["https://www.paguemenos.com.br/nossas-lojas"]
    is_playwright_spider = True
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS

    def parse(self, response: Response, **kwargs: Any) -> Any:
        # Collect cookies
        yield JsonRequest(
            "https://pmenos.paguemenos.com.br/wp-json/wp/v2/lojas?per_page=9999&page=1&order=asc",
            callback=self.parse_api,
        )

    def parse_api(self, response: Response, **kwargs: Any) -> Any:
        for location in json.loads(response.xpath("//text()").get()):
            item = Feature()
            item["ref"] = location["meta_box"]["id_loja"]
            item["website"] = location["link"]
            item["phone"] = location["meta_box"]["telefone"].split("/")[0]
            item["street_address"] = location["meta_box"]["endereco"]
            item["city"] = location["meta_box"]["cidade"]
            item["state"] = location["meta_box"]["uf"]
            item["postcode"] = location["meta_box"]["cep"]

            yield item
