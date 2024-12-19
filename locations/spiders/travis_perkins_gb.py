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
            url="https://www.travisperkins.co.uk/graphql?op=getAllBranches",
            data={
                "operationName": "getAllBranches",
                "variables": {"brandId": "tp", "input": {"first": 2000, "features": []}},
                "query": """query getAllBranches($brandId: ID!, $input: TpplcBranchSearchInput!) {
                tpplcBrand(brandId: $brandId) {
                  searchBranches(input: $input) {
                    edges {
                      ...TpplcBranchFields
                      __typename
                    }
                    __typename
                  }
                  __typename
                }
              }

              fragment TpplcBranchFields on TpplcBranch {
                name
                id
                address {
                  line1
                  line2
                  line3
                  town
                  postalCode
                  __typename
                }
                geoPoint {
                  latitude
                  longitude
                  __typename
                }
                branchSchedule {
                  openingTime
                  closingTime
                  dayOfWeek
                  closed
                  __typename
                }
                phone
                email
                manager
                features {
                  code
                  name
                  __typename
                }
                capabilities {
                  items {
                    ... on TpplcBenchmarx {
                      type
                      __typename
                    }
                    __typename
                  }
                  __typename
                }
                __typename
              }""",
            },
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["data"]["tpplcBrand"]["searchBranches"]["edges"]:
            item = DictParser.parse(location)
            item["street_address"] = merge_address_lines(
                [location["address"]["line1"], location["address"]["line2"], location["address"]["line3"]]
            )
            item["website"] = "https://www.travisperkins.co.uk/branch-locator/{}".format(location["id"])

            item["opening_hours"] = OpeningHours()
            for rule in location["branchSchedule"]:
                if rule["closed"]:
                    continue
                item["opening_hours"].add_range(rule["dayOfWeek"], rule["openingTime"], rule["closingTime"])
            if m := location["capabilities"]["items"]:
                if "Benchmarx" in m[0]["__typename"]:
                    item.update(self.BENCHMARX)

            yield item
