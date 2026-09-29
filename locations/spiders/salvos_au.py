from typing import AsyncIterator, Iterable

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class SalvosAUSpider(Spider):
    name = "salvos_au"
    item_attributes = {"brand": "Salvos", "brand_wikidata": "Q120646407"}

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield self.query_warehouses()

    def query_warehouses(self, after: str | None = None) -> JsonRequest:
        return JsonRequest(
            url="https://checkout.ssapi.link/graphql/",
            data={
                "query": """
                    query getWarehouses($after: String) {
                      warehouses(first: 100, after: $after) {
                        pageInfo {
                          hasNextPage
                          endCursor
                        }
                        edges {
                          node {
                            id
                            name
                            address {
                              streetAddress1
                              streetAddress2
                              city
                              postalCode
                              countryArea
                              phone
                            }
                          }
                        }
                      }
                    }
                """,
                "variables": {"after": after},
            },
        )

    def parse(self, response: Response) -> Iterable[Feature | JsonRequest]:
        warehouses = response.json()["data"]["warehouses"]
        if warehouses["pageInfo"]["hasNextPage"]:
            yield self.query_warehouses(warehouses["pageInfo"]["endCursor"])

        for edge in warehouses["edges"]:
            store = edge["node"]
            address = store.pop("address")
            if store["name"].startswith("Test ") or address["streetAddress1"] == "ONLINE STORE ONLY":
                continue
            store.update(address)

            item = DictParser.parse(store)
            item["branch"] = item.pop("name").split(", ")[0].strip()
            item["street_address"] = merge_address_lines([address["streetAddress1"], address["streetAddress2"]])
            item["state"] = address["countryArea"]
            apply_category(Categories.SHOP_CHARITY, item)
            yield item
