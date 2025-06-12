from typing import Any, Iterable

from scrapy import Request, Spider
from scrapy.http import JsonRequest, Response

from locations.dict_parser import DictParser
from locations.geo import city_locations


class SamsClubMXSpider(Spider):
    name = "sams_club_mx"
    item_attributes = {"brand": "Sam's Club", "brand_wikidata": "Q1972120"}

    def start_requests(self) -> Iterable[Request]:
        for city in city_locations("MX", 55000):
            yield JsonRequest(
                url="https://www.sams.com.mx/orchestra/graphql",
                method="POST",
                headers={
                    "content-type": "application/json",
                    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
                    "x-apollo-operation-name": "nearByNodes",
                    "x-o-bu": "SAMS-MX",
                    "x-o-gql-query": "query nearByNodes",
                    "x-o-platform-version": "main-1.186.0-ce7ca61-0407T2303",
                    "x-o-segment": "oaoh",
                },
                data={
                    "query": "query nearByNodes( $input:LocationInput! $checkItemAvailability:Boolean! $checkWeeklyReservation:Boolean! $enableStoreSelectorMarketplacePickup:Boolean! $enableVisionStoreSelector:Boolean! $enableStorePagesAndFinderPhase2:Boolean! $enableStoreBrandFormat:Boolean! ){nearByNodes(input:$input){nodes{id distance type isGlassEligible displayName name marketType storeBrandFormat @include(if:$enableStoreBrandFormat) address{addressLineOne addressLineTwo state city postalCode country}geoPoint @skip(if:$checkItemAvailability){latitude longitude}capabilities{accessPointId accessPointType geoPoint @skip(if:$checkItemAvailability){latitude longitude}expressEnabled isActive isTest assortmentNodeId timeZone}open24Hours displayAccessTypes isNodeSelectableOnline partnerId @include(if:$enableStoreSelectorMarketplacePickup) weeklyReservationDetails @include(if:$checkWeeklyReservation){slot{startTime displayValueStartTime}id}weeklyReservationCapability @include(if:$checkWeeklyReservation){supportsWeeklyReservation}operationalHours{day start closed end}product @include(if:$checkItemAvailability){availabilityStatus}services @include(if:$enableVisionStoreSelector){name phone displayName operationalHours{day start closed end}open24Hours}tempOperationalHours @include(if:$enableStorePagesAndFinderPhase2){date start end closed name}}}}",
                    "variables": {
                        "input": {
                            "postalCode": "11220",
                            "accessTypes": ["PICKUP_INSTORE", "PICKUP_CURBSIDE"],
                            "nodeTypes": ["STORE", "PICKUP_SPOKE", "PICKUP_POPUP"],
                            "latitude": city["latitude"],
                            "longitude": city["longitude"],
                            "radius": 1000000,
                        },
                        "checkItemAvailability": False,
                        "checkWeeklyReservation": False,
                        "enableStoreSelectorMarketplacePickup": False,
                        "enableVisionStoreSelector": False,
                        "enableStorePagesAndFinderPhase2": False,
                        "enableStoreBrandFormat": False,
                    },
                },
            )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        if data := response.json()["data"]["nearByNodes"]:
            for location in data["nodes"]:
                item = DictParser.parse(location)
                item["branch"] = item.pop("name", "").removeprefix("Sam's Club ")
                yield item
