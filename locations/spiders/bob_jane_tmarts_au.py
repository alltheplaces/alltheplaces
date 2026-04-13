from typing import Any, AsyncIterator

from scrapy.http import JsonRequest, Response
from scrapy.spiders import Spider

from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import merge_address_lines


class BobJaneTmartsAUSpider(Spider):
    name = "bob_jane_tmarts_au"
    item_attributes = {"brand": "Bob Jane T-Marts", "brand_wikidata": "Q16952468"}

    async def start(self) -> AsyncIterator[Any]:
        yield JsonRequest(
            url="https://www.bobjane.com.au/api/2026-01/graphql.json",
            data={"query": """{
              locations(first:250,sortKey:NAME) {
                edges {
                  node {
                    id
                    address {
                      phone
                      longitude
                      latitude
                      formatted
                      provinceCode
                    }
                    name
                  }
                }
              }
            }"""},
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["data"]["locations"]["edges"]:
            if location["node"]["name"].startswith("warehouse"):
                continue
            location.update(location.pop("node"))
            location.update(location.pop("address"))
            item = DictParser.parse(location)
            item["branch"] = item.pop("name")
            item["addr_full"] = merge_address_lines(location["formatted"])
            item["website"] = f"https://www.bobjane.com.au/pages/{item['branch'].lower().replace(' ','-')}-t-marts"
            yield item
