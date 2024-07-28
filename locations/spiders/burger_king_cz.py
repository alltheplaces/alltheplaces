from typing import Any, Iterable
from urllib.parse import urljoin

from scrapy import Request, Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Extras, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import merge_address_lines
from locations.spiders.burger_king import BURGER_KING_SHARED_ATTRIBUTES


class BurgerKingCZSpider(Spider):
    name = "burger_king_cz"
    item_attributes = BURGER_KING_SHARED_ATTRIBUTES
    allowed_domains = ["czqk28jt.api.sanity.io"]
    db = "prod_bk_cz"
    base = "https://burgerking.cz/store-locator/store/"

    def start_requests(self) -> Iterable[Request]:
        yield JsonRequest(
            url="https://czqk28jt.api.sanity.io/v2023-08-01/graphql/{}/gen3".format(self.db),
            data={
                "query": """
                query AllRestaurant {
                    allRestaurant(where: { environment: { eq: "prod" }, status: { eq: "Open" } }) {
                        hasDelivery
                        hasDineIn
                        hasTakeOut
                        hasDriveThru
                        ref: _id
                        phoneNumber
                        latitude
                        longitude
                        hasPlayground
                        hasWifi
                        isHalal
                        operator: franchiseGroupName
                        isDarkKitchen
                        address: physicalAddress {
                            address1
                            address2
                            city
                            state: stateProvinceShort
                            postalCode
                            country
                        }
                        diningRoomHours {
                            sunOpen
                            sunClose
                            monOpen
                            monClose
                            tueOpen
                            tueClose
                            wedOpen
                            wedClose
                            thrOpen
                            thrClose
                            friOpen
                            friClose
                            satOpen
                            satClose
                        }
                        driveThruHours {
                            sunOpen
                            sunClose
                            monOpen
                            monClose
                            tueOpen
                            tueClose
                            wedOpen
                            wedClose
                            thrOpen
                            thrClose
                            friOpen
                            friClose
                            satOpen
                            satClose
                        }
                    }
                }"""
            },
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["data"]["allRestaurant"]:
            item = DictParser.parse(location)
            item["street_address"] = merge_address_lines(
                [location["address"]["address1"], location["address"]["address2"]]
            )
            item["operator"] = location["operator"]
            item["website"] = urljoin(self.base, location["ref"])
            apply_yes_no(Extras.DELIVERY, item, location["hasDelivery"] is True)
            apply_yes_no(Extras.INDOOR_SEATING, item, location["hasDineIn"] is True)
            apply_yes_no(Extras.TAKEAWAY, item, location["hasTakeOut"] is True)
            apply_yes_no(Extras.DRIVE_THROUGH, item, location["hasDriveThru"] is True)
            apply_yes_no(Extras.WIFI, item, location["hasWifi"] is True)
            apply_yes_no(Extras.HALAL, item, location["isHalal"] is True)
            # isDarkKitchen

            if hours := location.get("diningRoomHours"):
                item["opening_hours"] = self.parse_hours(hours)
            if hours := location.get("driveThruHours"):
                item["extras"]["opening_hours:drive_through"] = self.parse_hours(hours).as_opening_hours()

            yield item

    def parse_hours(self, hours: dict) -> OpeningHours:
        oh = OpeningHours()
        for day in ["mon", "tue", "wed", "thr", "fri", "sat", "sun"]:
            if hours.get("{}Open".format(day)) and hours.get("{}Close".format(day)):
                oh.add_range(
                    day,
                    hours["{}Open".format(day)].removesuffix(".0000000"),
                    hours["{}Close".format(day)].removesuffix(".0000000"),
                    "1970-01-01 %H:%M:%S",
                )
        return oh
