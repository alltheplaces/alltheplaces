from typing import Any, Iterable

from scrapy import Request, Spider
from scrapy.http import JsonRequest, Response

from locations.dict_parser import DictParser


class ServiceApotheekNLSpider(Spider):
    name = "service_apotheek_nl"
    item_attributes = {"brand": "Service Apotheek", "brand_wikidata": "Q124129179"}

    def start_requests(self) -> Iterable[Request]:
        yield JsonRequest(
            "https://gate.serviceapotheek.nl/graphql",
            data={
                "query": """
            query GetLocators {
                locators {
                    type
                    geometry {
                        type
                        coordinates
                    }
                    properties {
                        name
                        ref: store_code
                        enabled
                        has_shop
                        address {
                            house_number
                            street
                            city
                            postcode
                            phone
                        }
                    }
                }
            }"""
            },
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["data"]["locators"]:
            if not location["properties"]["enabled"]:
                continue
            item = DictParser.parse(location["properties"])
            item["geometry"] = location["geometry"]
            item["website"] = "https://www.serviceapotheek.nl/{}/".format(location["properties"]["ref"])
            yield item
