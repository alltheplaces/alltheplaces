from typing import AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.items import Feature


class HeringBRSpider(Spider):
    name = "hering_br"
    item_attributes = {"brand": "Hering", "brand_wikidata": "Q5119055"}

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(
            url="https://www.hering.com.br/_v/public/graphql/v1",
            data={
                "query": """
                query getStores {
                 documents(acronym: "BA", fields: ["cep", "cidade", "rua", "telefones", "bairro", "nome"],
                                            where: "cidade=*", pageSize: 1000)
                                            {
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
            store = {}
            for field in data["fields"]:
                value = field.get("value", "null")
                if not value == "null":
                    store[field["key"]] = value
            item = Feature()
            item["ref"] = store.get("id")
            item["branch"] = store.get("nome").replace("Hering ", "").replace("HERING ", "")
            item["city"] = store.get("cidade")
            item["street_address"] = store.get("rua")
            item["postcode"] = store.get("cep")
            item["phone"] = store.get("telefones")
            apply_category(Categories.SHOP_CLOTHES, item)
            yield item
