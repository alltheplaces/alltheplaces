from typing import AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import OpeningHours, day_range, sanitise_day


class OldChicagoUSSpider(Spider):
    name = "old_chicago_us"
    item_attributes = {"brand": "Old Chicago", "brand_wikidata": "Q64411347"}

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(
            url="https://oc-api-prod.azurewebsites.net/graphql",
            data={"query": """query {
                    viewer {
                        locations {
                            edges {
                                node {
                                    title
                                    comingSoon
                                    ref: locationId
                                    slug
                                    expireAt
                                    menuURL
                                    address {
                                        full: raw
                                        streetNumber
                                        street: route
                                        city
                                        stateCode
                                        postalCode
                                    }
                                    simpleHours {
                                        days
                                        hours
                                    }
                                    email
                                    fax
                                    latitude
                                    longitude
                                }
                            }
                        }
                    }
                }"""},
        )

    def parse(self, response, **kwargs):
        for edge in response.json()["data"]["viewer"]["locations"]["edges"]:
            location = edge["node"]
            if location["comingSoon"]:
                continue

            item = DictParser.parse(location)
            item["addr_full"] = location["address"]["full"]
            item["street_address"] = " ".join([item["housenumber"], item["street"]])
            item["website"] = f'https://oldchicago.com/locations/{location["slug"]}'

            item["opening_hours"] = OpeningHours()
            for rule in location["simpleHours"]:
                if "-" in rule["days"]:
                    start_day, end_day = rule["days"].split("-")
                else:
                    start_day = end_day = rule["days"]
                start_day = sanitise_day(start_day)
                end_day = sanitise_day(end_day)
                start_time, end_time = rule["hours"].split("-")
                item["opening_hours"].add_days_range(
                    day_range(start_day, end_day), start_time, end_time, time_format="%I:%M%p"
                )

            yield item
