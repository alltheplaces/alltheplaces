from typing import Any, Iterable

from scrapy import Request, Spider
from scrapy.http import JsonRequest, Response

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class PeaveyMartCASpider(Spider):
    name = "peavey_mart_ca"
    item_attributes = {"brand": "Peavey Mart", "brand_wikidata": "Q7158483"}
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def start_requests(self) -> Iterable[Request]:
        yield JsonRequest(
            url="https://www.peaveymart.com/api/graphql",
            data={
                "query": """{
                    spLocations(pageSize: 200) {
                        items {
                            ref: code
                            name
                            phone
                            locationTypes {
                                code
                                name
                            }
                            address {
                                street_address: address1
                                city: cityOrTown
                                state: stateOrProvince
                                postcode: postalOrZipCode
                                countryCode
                            }
                            geo {
                                lat
                                lng
                            }
                            fulfillmentTypes {
                                code
                                name
                            }
                            regularHours {
                                monday {
                                    openTime
                                    closeTime
                                    isClosed
                                }
                                tuesday {
                                    openTime
                                    closeTime
                                    isClosed
                                }
                                wednesday {
                                    openTime
                                    closeTime
                                    isClosed
                                }
                                thursday {
                                    openTime
                                    closeTime
                                    isClosed
                                }
                                friday {
                                    openTime
                                    closeTime
                                    isClosed
                                }
                                saturday {
                                    openTime
                                    closeTime
                                    isClosed
                                }
                                sunday {
                                    openTime
                                    closeTime
                                    isClosed
                                }
                            }
                            attributes {
                                fullyQualifiedName
                                attributeDefinitionId
                                values
                            }
                        }
                    }
                }"""
            },
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["data"]["spLocations"]["items"]:
            item = DictParser.parse(location)
            for attribute in location["attributes"]:
                if attribute["fullyQualifiedName"] == "tenant~store-email-address":
                    item["email"] = "; ".join(attribute["values"])

            item["opening_hours"] = OpeningHours()
            for day, rule in location["regularHours"].items():
                if rule["isClosed"] is True:
                    item["opening_hours"].set_closed(day)
                else:
                    item["opening_hours"].add_range(day, rule["openTime"], rule["closeTime"])

            if item["name"].startswith("Peavey Mart"):
                item["branch"] = item.pop("name").removeprefix("Peavey Mart").strip()
            else:
                continue

            yield item
