import json
from typing import Any, AsyncIterator

from scrapy.http import JsonRequest, TextResponse

from locations.dict_parser import DictParser
from locations.geo import city_locations
from locations.hours import OpeningHours
from locations.playwright_spider import PlaywrightSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS


class CaseysGeneralStoreSpider(PlaywrightSpider):
    name = "caseys_general_store"
    item_attributes = {"brand": "Casey's General Store", "brand_wikidata": "Q2940968"}
    requires_proxy = True
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS

    async def start(self) -> AsyncIterator[Any]:
        url = "https://www.caseys.com/api/graphql"

        for city in city_locations("US", 10000):
            payload = {
                "operationName": "GetStoresByFilters",
                "variables": {
                    "input": {"latitude": f"{city['latitude']}", "longitude": f"{city['longitude']}"},
                    "occasionType": "CARRYOUT",
                    "carryoutType": None,
                    "withTimeSlots": True,
                },
                "extensions": {"clientLibrary": {"name": "@apollo/client", "version": "4.1.9"}},
                "query": """query GetStoresByFilters($input: StoresByCoordinateInput!, $occasionType: OccasionType!, $carryoutType: CarryoutType, $withTimeSlots: Boolean!) {
              storesByCoordinate(input: $input) {
                formattedDistance
                store {
                  storeNumber
                  name
                  shortName
                  displayName
                  brand
                  address {
                    id
                    line1
                    city
                    stateAbbreviation
                    postalCode
                    phoneNumber
                  }
                  geoPoint {
                    latitude
                    longitude
                  }
                  amenities {
                    key
                    value
                    isEnabled
                  }
                  storeOpenHours
                  carryoutHours
                  curbsideHours
                  deliveryHours
                  carwashHours
                  locationUrl
                  hours {
                    type
                    hours {
                      dayOfWeek
                      blocks {
                        openDateTime
                        closeDateTime
                      }
                    }
                  }
                  timeZoneId
                  availableTimeSlots(occasionType: $occasionType, carryoutType: $carryoutType) @include(if: $withTimeSlots) {
                    displayText
                    option
                    enabled
                    timeSlots {
                      displayText
                      value
                    }
                  }
                  onlineOrdering
                  onlineOrderingTemporarilyUnavailable
                  deliveryDisruption
                }
              }
            }""",
            }

            yield JsonRequest(
                url=url,
                method="POST",
                data=payload,
                callback=self.parse,
            )

    def parse(self, response: TextResponse, **kwargs):
        for location in json.loads(response.xpath("//pre//text()").get())["data"]["storesByCoordinate"]:
            location.update(location.pop("store"))
            item = DictParser.parse(location)
            item.pop("name")
            item["branch"] = location["displayName"]
            item["website"] = item["ref"] = response.urljoin(item["website"])
            oh = OpeningHours()
            for day_time in location["storeOpenHours"]:
                oh.add_ranges_from_string(day_time)
            item["opening_hours"] = oh
            yield item
