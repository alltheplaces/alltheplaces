from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.dict_parser import DictParser


class MontblancSpider(Spider):
    name = "montblanc"
    item_attributes = {"brand": "Montblanc", "brand_wikidata": "Q142691"}

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(
            url="https://stores.montblanc.com/graphql",
            data={
                "query": """
                query PublicBoutiques {
                    publicBoutiques {
                        id
                        latitude
                        longitude
                        branch: defaultName
                        phone
                        email
                        fax
                        city {
                            country {
                                defaultName
                            }
                        }
                        openTimes {
                            endDay
                            endTime
                            startDay
                            startTime
                        }
                        state {
                            defaultName
                        }
                        type {
                            defaultName
                        }
                    }
                }"""
            },
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["data"]["publicBoutiques"]:
            if location["type"]["defaultName"] not in ["Boutique", "Outlet"]:
                continue

            item = DictParser.parse(location)
            item["city"] = None
            item["state"] = (location.get("state") or {}).get("defaultName")
            item["country"] = ((location.get("city") or {}).get("country") or {}).get("defaultName")
            item["website"] = "https://stores.montblanc.com/boutique/{}".format(location["id"])

            yield item
