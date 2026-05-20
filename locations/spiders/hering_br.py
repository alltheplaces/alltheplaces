from typing import AsyncIterator, Any

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.items import Feature


class HeringBRSpider(Spider):
    name = "hering_br"
    item_attributes = {"brand": "Hering", "brand_wikidata": "Q5119055"}

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(
            url="https://www.hering.com.br/_v/public/graphql/v1",
            data={"query": """
                query getStores {
                 documents(acronym: "BA", fields: ["cep", "cidade", "rua", "telefones", "bairro", "nome"],
                                            where: "cidade=*", pageSize: 1000)
                                            {
                                            fields {
                                                    key
                                                    value
                                                   }
                                            }
                                        }"""},
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for data in response.json()["data"]["documents"]:
            store = {}
            for field in data["fields"]:
                value = field.get("value", "null")
                if not value == "null":
                    store[field["key"]] = value
            item = Feature()
            item["ref"] = store.get("id")
            if name := store.get("nome"):
                if name.startswith("Hering Kids "):
                    item["branch"] = name.removeprefix("Hering Kids ").removeprefix("Shopping ")
                    item["name"] = "Hering Kids"
                elif name.startswith("Hering Mega Store "):
                    item["branch"] = name.removeprefix("Hering Mega Store ").removeprefix("Shopping ")
                    item["name"] = "Hering Mega Store"
                elif name.startswith("Hering Outlet "):
                    item["branch"] = name.removeprefix("Hering Outlet ")
                    item["name"] = "Hering Outlet"
                elif name.startswith("Hering Store "):
                    item["branch"] = name.removeprefix("Hering Store ").removeprefix("Shopping ")
                    item["name"] = "Hering"

            item["city"] = store.get("cidade")
            item["street_address"] = store.get("rua")
            item["postcode"] = store.get("cep")
            item["phone"] = store.get("telefones", "").replace(",", "; ")
            apply_category(Categories.SHOP_CLOTHES, item)
            yield item
