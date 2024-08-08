from scrapy import Spider
from scrapy.http import JsonRequest

from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class ChiquinhoSorvetesBRSpider(Spider):
    name = "chiquinho_sorvetes_br"
    item_attributes = {"brand": "Chiquinho Sorvetes", "brand_wikidata": "Q65164356"}

    def start_requests(self):
        yield JsonRequest(
            url="https://www.itfgestor.com.br/ITFWebServiceSiteChiquinho/estado?key=f3a06f73b2d8dc7c3befe2c287981418",
            callback=self.parse_states,
        )

    def parse_states(self, response, **kwargs):
        for state in response.json():
            yield JsonRequest(
                url=f'https://www.itfgestor.com.br/ITFWebServiceSiteChiquinho/cidade/{state["sigla"]}?key=cff6872cbdef2dcf71b161ff88965467',
                callback=self.parse_state,
            )

    def parse_state(self, response, **kwargs):
        for city in response.json():
            yield JsonRequest(
                url=f'https://www.itfgestor.com.br/ITFWebServiceSiteChiquinho/franquia/{city["codigoIbge"]}?key=f49ab097bcb1168cf755ad28dd8349c7'
            )

    def parse(self, response, **kwargs):
        for location in response.json():
            item = Feature()
            item["ref"] = location["codigo"]
            item["name"] = location["nome"]
            item["street_address"] = merge_address_lines([location.get("complemento"), location["endereco"]])
            item["postcode"] = location["cep"]
            item["phone"] = location["telefone"]

            yield item
