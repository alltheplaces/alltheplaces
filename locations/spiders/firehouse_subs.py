import re
from typing import Any, Iterable

from scrapy import Request, Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Extras, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import DAYS_3_LETTERS, OpeningHours
from locations.pipelines.address_clean_up import merge_address_lines


class FirehouseSubsSpider(Spider):
    name = "firehouse_subs"
    item_attributes = {"brand": "Firehouse Subs", "brand_wikidata": "Q5451873"}

    def make_request(self, country: str, offset: int, limit: int = 50) -> JsonRequest:
        return JsonRequest(
            url=f"https://czqk28jt.apicdn.sanity.io/v1/graphql/prod_fhs_{country}/default",
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
                thuClose: thrClose
                thuOpen: thrOpen
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
            meta=dict(country=country, offset=offset, limit=limit),
        )

    def start_requests(self) -> Iterable[Request]:
        for country in ["us", "ca"]:
            yield self.make_request(country, 0)

    def parse(self, response: Response, **kwargs: Any) -> Any:
        country = response.meta["country"]
        if locations := response.json()["data"].get("allRestaurants"):
            for location in locations:
                if location["status"] != "Open":
                    continue
                item = DictParser.parse(location)
                item["street_address"] = merge_address_lines(
                    [location["address"]["address1"], location["address"]["address2"]]
                )
                item["branch"] = item.pop("name")
                if isinstance(item["email"], list):
                    item["email"] = ";".join(item["email"])
                if location["operator_id"]:
                    item["operator"] = location["operator"]
                    item["extras"]["operator:ref"] = str(location["operator_id"])
                item["country"] = country
                item["website"] = f'https://www.firehousesubs.{country}/store-locator/store/{item["ref"]}'.replace(
                    ".us", ".com"
                )
                if hours := location["diningRoomHours"]:
                    item["opening_hours"] = OpeningHours()
                    for day in DAYS_3_LETTERS:
                        day = day.lower()
                        open_time = self.extract_time(hours.get(f"{day}Open"))
                        close_time = self.extract_time(hours.get(f"{day}Close"))

                        if open_time and close_time:
                            item["opening_hours"].add_range(day, open_time, close_time, "%H:%M:%S")

                apply_yes_no(Extras.TAKEAWAY, item, location["hasTakeOut"])
                apply_yes_no(Extras.DRIVE_THROUGH, item, location["hasDriveThru"], False)
                apply_yes_no(Extras.INDOOR_SEATING, item, location["hasDineIn"], False)
                apply_yes_no(Extras.DELIVERY, item, location["hasDelivery"], False)
                apply_yes_no(Extras.WIFI, item, location["hasWifi"], False)
                apply_yes_no(Extras.HALAL, item, location["isHalal"])
                apply_yes_no(Extras.KIDS_AREA, item, location.get("hasPlayground"), False)
                apply_yes_no(Extras.BREAKFAST, item, location.get("hasBreakfast"), False)
                yield item
            yield self.make_request(country, response.meta["offset"] + response.meta["limit"])

    @staticmethod
    def extract_time(time_str: str) -> str:
        match = re.search(r"(\d{2}:\d{2}:\d{2})", time_str) if time_str else None
        return match.group(1) if match else ""
