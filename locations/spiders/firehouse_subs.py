from typing import Any, Iterable

from scrapy import Request, Spider
from scrapy.http import JsonRequest, Response

from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import merge_address_lines


class FirehouseSubsSpider(Spider):
    name = "firehouse_subs"
    item_attributes = {"brand": "Firehouse Subs", "brand_wikidata": "Q5451873"}
    offset = 0
    limit = 50

    def make_request(self, offset: int, limit: int = limit) -> JsonRequest:
        return JsonRequest(
            url="https://czqk28jt.apicdn.sanity.io/v1/graphql/prod_fhs_us/default",
            data={
                "operationName": "GetRestaurants",
                "query": """
                query GetRestaurants($offset: Int, $limit: Int) {allRestaurants(offset: $offset, limit: $limit) {
                ref:_id
                environment
                chaseMerchantId
                diningRoomHours {
                friClose
                friOpen
                monClose
                monOpen
                satClose
                satOpen
                sunClose
                sunOpen
                thrClose
                thrOpen
                tueClose
                tueOpen
                wedClose
                wedOpen
                }
                driveThruLaneType
                email
                operator: franchiseGroupName
                operator_id: franchiseGroupId
                frontCounterClosed
                hasBreakfast
                hasBurgersForBreakfast
                hasCurbside
                hasDineIn
                hasCatering
                hasDelivery
                hasDriveThru
                hasMobileOrdering
                hasParking
                hasPlayground
                hasTakeOut
                hasWifi
                hasLoyalty
                hasPickupWindow
                isHalal
                latitude
                longitude
                mobileOrderingStatus
                name
                number
                parkingType
                phoneNumber
                playgroundType
                address: physicalAddress {
                  address1
                  address2
                  city
                  country
                  postalCode
                  state: stateProvinceShort
                }
                status
                vatNumber
              }
            }
            """,
                "variables": {"offset": offset, "limit": limit},
            },
        )

    def start_requests(self) -> Iterable[Request]:
        yield self.make_request(self.offset)

    def parse(self, response: Response, **kwargs: Any) -> Any:
        if locations := response.json()["data"].get("allRestaurants"):
            for location in locations:
                if location["status"] != "Open":
                    continue
                item = DictParser.parse(location)
                item["street_address"] = merge_address_lines(
                    [location["address"]["address1"], location["address"]["address2"]]
                )
                yield item
            self.offset += self.limit
            yield self.make_request(self.offset)
