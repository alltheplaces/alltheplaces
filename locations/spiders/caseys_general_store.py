import json
from typing import Any, AsyncIterator

import scrapy
from scrapy import Spider
from scrapy.http import TextResponse

from locations.dict_parser import DictParser
from locations.geo import city_locations
from locations.hours import OpeningHours


class CaseysGeneralStoreSpider(Spider):
    name = "caseys_general_store"
    item_attributes = {"brand": "Casey's General Store", "brand_wikidata": "Q2940968"}
    requires_proxy = True

    async def start(self) -> AsyncIterator[Any]:
        for city in city_locations("US", 10000):
            payload = {
                "operationName": "GetStoresByFilters",
                "variables": {
                    "input": {"latitude": f"{city['latitude']}", "longitude": f"{city['longitude']}"},
                    "occasionType": "CARRYOUT",
                    "withTimeSlots": True,
                },
                "extensions": {"clientLibrary": {"name": "@apollo/client", "version": "4.1.9"}},
                "query": "query GetStoresByFilters($input: StoresByCoordinateInput!, $occasionType: OccasionType!, $carryoutType: CarryoutType, $withTimeSlots: Boolean!) {\n  storesByCoordinate(input: $input) {\n    formattedDistance\n    store {\n      storeNumber\n      name\n      shortName\n      displayName\n      brand\n      brandLogo {\n        url\n        altText\n        __typename\n      }\n      address {\n        id\n        line1\n        city\n        stateAbbreviation\n        postalCode\n        phoneNumber\n        __typename\n      }\n      geoPoint {\n        latitude\n        longitude\n        __typename\n      }\n      amenities {\n        key\n        value\n        isEnabled\n        __typename\n      }\n      amenityGroups {\n        code\n        displayName\n        displayOrder\n        amenities {\n          displayName\n          code\n          displayOrder\n          value {\n            ... on BooleanAmenityValue {\n              value\n              __typename\n            }\n            __typename\n          }\n          __typename\n        }\n        __typename\n      }\n      storeOpenHours\n      carryoutHours\n      curbsideHours\n      carryoutWaitTime\n      deliveryWaitTime\n      deliveryHours\n      carwashHours\n      locationUrl\n      hours {\n        type\n        hours {\n          dayOfWeek\n          blocks {\n            openDateTime\n            closeDateTime\n            closeTime {\n              hour\n              minute\n              __typename\n            }\n            openTime {\n              minute\n              hour\n              __typename\n            }\n            __typename\n          }\n          __typename\n        }\n        __typename\n      }\n      timeZoneId\n      availableTimeSlots(occasionType: $occasionType, carryoutType: $carryoutType) @include(if: $withTimeSlots) {\n        displayText\n        option\n        enabled\n        timeSlots {\n          displayText\n          value\n          __typename\n        }\n        __typename\n      }\n      onlineOrdering\n      onlineOrderingTemporarilyUnavailable\n      deliveryDisruption\n      __typename\n    }\n    __typename\n  }\n}",
            }

            yield scrapy.Request(
                url="https://www.caseys.com/api/graphql",
                method="POST",
                body=json.dumps(payload),
                callback=self.parse,
            )

    def parse(self, response: TextResponse, **kwargs):
        for location in response.json()["data"]["storesByCoordinate"]:
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
