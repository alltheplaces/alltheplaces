import json

from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser

BRAND_MAPPING = {
    "Ipiranga": {"brand": "Ipiranga", "brand_wikidata": "Q2081136"},
    "Shell": {"brand": "Shell", "brand_wikidata": "Q110716465"},
    "SIM": {"brand": "SIM", "brand_wikidata": "Q132146636"},
    "BR": {"brand": "BR", "brand_wikidata": "Q4836468"},
}


class SimBRSpider(Spider):
    name = "sim_br"

    start_urls = ["https://www.simrede.com.br/unidades"]

    def parse(self, response):
        stations = json.loads(response.text)

        for station in stations:
            item = DictParser.parse(station)
            item["city"] = station.get("cidade")
            item["state"] = station.get("estado")
            item["street_address"] = station.get("logradouro")
            item["phone"] = station.get("contato")

            if station.get("bandeira") in BRAND_MAPPING:
                item["brand"] = BRAND_MAPPING[station.get("bandeira")]["brand"]
                item["brand_wikidata"] = BRAND_MAPPING[station.get("bandeira")]["brand_wikidata"]
            else:
                item["brand"] = station.get("bandeira")

            item["extras"]["source"] = station

            apply_category(Categories.FUEL_STATION, item)
            yield item
