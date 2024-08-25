from typing import Any, Iterable

from scrapy import Request, Spider
from scrapy.http import JsonRequest, Response

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import merge_address_lines


class TravisPerkinsGBSpider(Spider):
    name = "travis_perkins_gb"
    item_attributes = {"brand": "Travis Perkins", "brand_wikidata": "Q2450664"}
    BENCHMARX = {"brand": "Benchmarx", "brand_wikidata": "Q102181127"}

    def start_requests(self) -> Iterable[Request]:
        yield JsonRequest(
            url="https://www.travisperkins.co.uk/graphql",
            data={
                "query": """
                    query Branches {
                        branches {
                            ref: code
                            email
                            fax
                            branch: name
                            phone
                            address {
                                line1
                                line2
                                line3
                                city: town
                                postalCode
                            }
                            branchSchedule {
                                closed
                                closingTime
                                dayOfWeek
                                openingTime
                            }
                            location: geoPoint {
                                latitude
                                longitude
                            }
                        }
                    }"""
            },
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["data"]["branches"]:
            item = DictParser.parse(location)
            item["branch"] = location["branch"]
            item["street_address"] = merge_address_lines(
                [location["address"]["line1"], location["address"]["line2"], location["address"]["line3"]]
            )
            item["website"] = "https://www.travisperkins.co.uk/branch-locator/{}".format(location["ref"])
            item["extras"]["fax"] = location["fax"]

            item["opening_hours"] = OpeningHours()
            for rule in location["branchSchedule"]:
                if rule["closed"]:
                    continue
                item["opening_hours"].add_range(rule["dayOfWeek"], rule["openingTime"], rule["closingTime"])

            if " BENCHMARX" in item["branch"]:
                # Usually ends with "BENCHMARX KITCHENS & JOINERY", but sometimes spelt wrong
                item["branch"] = item["branch"].split(" BENCHMARX")[0]
                item.update(self.BENCHMARX)

            yield item
