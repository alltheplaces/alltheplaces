from typing import Any, Iterable

from scrapy import Request
from scrapy.http import JsonRequest, Response
from scrapy.spiders import Spider

from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours
from locations.user_agents import BROWSER_DEFAULT


class JumboNLSpider(Spider):
    name = "jumbo_nl"
    item_attributes = {"brand": "Jumbo", "brand_wikidata": "Q2262314"}
    start_urls = ["https://www.jumbo.com/api/graphql"]
    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "USER_AGENT": BROWSER_DEFAULT,
    }
    requires_proxy = True

    def make_request(self, page: int, size: int = 30) -> JsonRequest:
        return JsonRequest(
            url="https://www.jumbo.com/api/graphql",
            data={
                "operationName": "GetStoreList",
                "variables": {
                    "input": {
                        "latitude": "52.156108",
                        "longitude": "5.387825",
                        "distance": 1000,
                        "size": size,
                        "page": page,
                        "locationTypes": ["PICK_UP_POINT", "SUPERMARKET", "SUPERMARKET_PICK_UP_POINT"],
                    }
                },
                "query": """query GetStoreList($input: StoresByCoordinatesInput!) {
                            storesByCoordinates(input: $input) {
                                stores {
                                    openingHours {
                                        exceptions {
                                            startsOn
                                            endsOn
                                        }
                                        friday {
                                            closesAt
                                            opensAt
                                        }
                                        monday {
                                            closesAt
                                            opensAt
                                        }
                                        saturday {
                                            closesAt
                                            opensAt
                                        }
                                        sunday {
                                            closesAt
                                            opensAt
                                        }
                                        thursday {
                                            closesAt
                                            opensAt
                                        }
                                        tuesday {
                                            closesAt
                                            opensAt
                                        }
                                        wednesday {
                                            closesAt
                                            opensAt
                                        }
                                    }
                                    name
                                    location {
                                        latitude
                                        longitude
                                        address {
                                            street
                                            houseNumber
                                            city
                                            postalCode
                                        }
                                    }
                                    facilities {
                                        locationType
                                    }
                                    distance
                                    websiteURL
                                    storeId
                                    commerce {
                                        inStore {
                                            available
                                        }
                                        homeDelivery {
                                            available
                                        }
                                        collection {
                                            available
                                        }
                                    }
                                }
                                totalCount
                                totalPages
                                page
                            }
                        }""",
            },
        )

    def start_requests(self) -> Iterable[Request]:
        yield self.make_request(0)

    def parse(self, response: Response, **kwargs: Any) -> Any:
        stores_info = response.json()["data"]["storesByCoordinates"]
        for store in stores_info["stores"]:
            item = DictParser.parse(store)
            item["opening_hours"] = OpeningHours()
            for day in DAYS_FULL:
                time = store["openingHours"][day.lower()]
                if open_time := time["opensAt"]:
                    open_time = open_time.replace(":00.000Z", "")
                if close_time := time["closesAt"]:
                    close_time = close_time.replace(":00.000Z", "")
                item["opening_hours"].add_range(day=day, open_time=open_time, close_time=close_time)
            yield item

        if stores_info["page"] < stores_info["totalPages"] - 1:  # page starts from zero
            yield self.make_request(stores_info["page"] + 1)
