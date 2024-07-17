from typing import Any, Iterable

from scrapy import Request, Spider
from scrapy.http import JsonRequest, Response

from locations.dict_parser import DictParser
from locations.hours import OpeningHours, day_range


class MontblancSpider(Spider):
    name = "montblanc"
    item_attributes = {"brand": "Montblanc", "brand_wikidata": "Q142691"}

    def start_requests(self) -> Iterable[Request]:
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

            item["opening_hours"] = OpeningHours()
            for rule in location["openTimes"]:
                item["opening_hours"].add_days_range(
                    day_range(rule["startDay"], rule["endDay"]), rule["startTime"], rule["endTime"]
                )

            yield item
