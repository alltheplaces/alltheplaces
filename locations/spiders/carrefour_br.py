import scrapy
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser

BRANDS = {
    "hiper": ("Carrefour", "Q217599", Categories.SHOP_SUPERMARKET),
    "bairro": ("Carrefour Bairro", "Q17490905", Categories.SHOP_SUPERMARKET),
    "market": ("Carrefour Market", "Q2689639", Categories.SHOP_SUPERMARKET),
    "express": ("Carrefour Express", "Q2940190", Categories.SHOP_CONVENIENCE),
    "drogaria": ("Carrefour Drogaria", "", Categories.PHARMACY),
    "posto": ("Carrefour Posto", "", Categories.FUEL_STATION),
}


class CarrefourBRSpider(scrapy.Spider):
    name = "carrefour_br"

    def start_requests(self):
        yield JsonRequest(
            url="https://www.carrefour.com.br/_v/public/graphql/v1",
            data={
                "query": """query {
                  documents(acronym:"LO",fields:["id","lat","lng","logradouro","loja","numero","complemento","cep","cidade","uf","tipo"],pageSize:1000) {
                      fields {
                            key
                            value
                        }
                    }
                }"""
            },
        )

    def parse(self, response, **kwargs):
        for data in response.json()["data"]["documents"]:
            store = {field["key"]: field["value"] for field in data["fields"] if not field["value"] == "null"}
            store["name"] = store.get("loja")
            store["city"] = store.get("cidade")
            store["street"] = store.get("logradouro")
            store["street-number"] = store.get("numero")
            store["postal_code"] = store.get("cep")
            store["city"] = store.get("cidade")
            store["state"] = store.get("uf")
            lat = store.get("lat")
            lon = store.get("lng")
            store["lat"] = round(int(lat) * (10 ** (-(len(lat) - 2))), 9) * (-1) if lat else None
            store["lon"] = round(int(lon) * (10 ** (-(len(lon) - 2))), 9) * (-1) if lon else None
            item = DictParser.parse(store)
            brand_type = store.get("tipo")
            if not brand_type:
                for key in BRANDS:
                    if key in item["name"].lower():
                        brand_type = key
                        break
            item["brand"], item["brand_wikidata"], category = BRANDS.get(brand_type, ("", "", None))
            if category is not None:
                apply_category(category, item)
            yield item
