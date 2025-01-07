from copy import deepcopy
from typing import Any, Iterable

from scrapy import Request, Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.geo import postal_regions
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import merge_address_lines


class GiantEagleUSSpider(Spider):
    name = "giant_eagle_us"
    GIANT_EAGLE = {"brand": "Giant Eagle", "brand_wikidata": "Q1522721"}
    GET_GO = {"brand": "GetGo", "brand_wikidata": "Q5553766"}
    MARKET_DISTRICT = {"brand": "Market District", "brand_wikidata": "Q98550869"}

    def make_request(self, zipcode: str, cursor: str = "", count: int = 20) -> JsonRequest:
        return JsonRequest(
            url="https://core.shop.gianteagle.com/api/v2",
            data={
                "operationName": "GetStores",
                "variables": {
                    "count": count,
                    "storeBrowsingModes": ["pickup", "delivery", "instore"],
                    "zipcode": zipcode,
                    "cursor": cursor,
                },
                "query": """query GetStores($zipcode: ZipCode!, $storeBrowsingModes: [BrowsingMode!], $count: Int, $cursor: String) {
                    stores(zipcode: $zipcode, storeBrowsingModes: $storeBrowsingModes, first: $count, after: $cursor) {
                        edges {
                            cursor
                            node {
                                address {
                                    fullAddress
                                    street
                                    street2
                                    city
                                    state
                                    zipcode
                                    location {
                                        lat
                                        lng
                                    }
                                }
                                availableServices {
                                    delivery
                                    instore
                                    pickup
                                    scanPayGoLegacy
                                }
                                ref:code
                                currentAvailability {
                                    holidayName
                                    label
                                    status
                                }
                                customerCareNumber
                                departments {
                                    currentAvailability {
                                        holidayName
                                        label
                                        status
                                    }
                                    hours {
                                        dayOfWeek
                                        holidayName
                                        label
                                    }
                                    id
                                    links {
                                        id
                                        label
                                        url
                                    }
                                    name
                                    phoneNumber {
                                        number
                                        numberWithoutInternationalization
                                        prettyNumber
                                    }
                                }
                                hours {
                                    dayOfWeek
                                    holidayName
                                    label
                                }
                                id
                                name
                                phoneNumber {
                                    number
                                    numberWithoutInternationalization
                                    prettyNumber
                                }
                                slug
                                timeSlotsSummary {
                                    fulfillmentMethod
                                    nextAvailableAt {
                                        date
                                        time
                                        timestamp
                                    }
                                    throughDate
                                }
                            }
                        }
                        pageInfo {
                            endCursor
                            hasNextPage
                        }
                    }
                }""",
            },
            cb_kwargs=dict(zipcode=zipcode),
        )

    def start_requests(self) -> Iterable[Request]:
        for index, record in enumerate(postal_regions("US")):
            if index % 25 == 0:
                yield self.make_request(zipcode=record["postal_region"])

    @staticmethod
    def parse_hours(hours: [dict]) -> OpeningHours:
        opening_hours = OpeningHours()
        for hour in hours:
            opening_hours.add_ranges_from_string(f'{hour["dayOfWeek"]} {hour["label"]}')
        return opening_hours

    def parse(self, response: Response, zipcode: str) -> Any:
        for location in response.json()["data"]["stores"]["edges"]:
            location_info = location["node"]
            location_info.update(location_info.pop("address"))
            location_info["street-address"] = merge_address_lines(
                [location_info.pop("street"), location_info.pop("street2")]
            )
            item = DictParser.parse(location_info)
            item["addr_full"] = location_info["fullAddress"]
            item["website"] = f'https://www.gianteagle.com/stores/{location_info["ref"]}'

            for department in location_info["departments"]:
                if "Pharmacy" in department["name"]:
                    pharmacy = deepcopy(item)
                    pharmacy["brand"] = "Giant Eagle Pharmacy"
                    pharmacy["name"] = department["name"]
                    pharmacy["ref"] = department["id"] + "-pharmacy"
                    pharmacy["opening_hours"] = self.parse_hours(department["hours"])
                    pharmacy["phone"] = department["phoneNumber"]["number"] if department["phoneNumber"] else None
                    apply_category(Categories.PHARMACY, pharmacy)
                    yield pharmacy

                if "GetGo" in department["name"]:
                    convenience_store = deepcopy(item)
                    convenience_store["name"] = department["name"]
                    convenience_store["ref"] = department["id"] + "-store"
                    convenience_store["opening_hours"] = self.parse_hours(department["hours"])
                    convenience_store["phone"] = (
                        department["phoneNumber"]["number"] if department["phoneNumber"] else None
                    )
                    convenience_store.update(self.GET_GO)
                    apply_category(Categories.SHOP_CONVENIENCE, convenience_store)
                    yield convenience_store

            item["phone"] = location_info["phoneNumber"]["number"] if location_info["phoneNumber"] else None
            item["opening_hours"] = self.parse_hours(location_info["hours"])

            if "Market District" in item["name"]:
                item.update(self.MARKET_DISTRICT)
            else:
                item.update(self.GIANT_EAGLE)
            apply_category(Categories.SHOP_SUPERMARKET, item)

            yield item

        page_info = response.json()["data"]["stores"]["pageInfo"]
        if page_info.get("hasNextPage"):
            yield self.make_request(zipcode=zipcode, cursor=page_info["endCursor"])
