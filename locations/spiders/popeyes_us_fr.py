from typing import Any, Iterable
from urllib.parse import urljoin

from scrapy import Request
from scrapy.http import JsonRequest, Response
from scrapy.spiders import Spider

from locations.categories import Extras, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.pipelines.address_clean_up import merge_address_lines


class PopeyesUSFRSpider(Spider):
    name = "popeyes_us_fr"
    item_attributes = {"brand": "Popeyes", "brand_wikidata": "Q1330910"}

    def start_requests(self) -> Iterable[Request]:
        for country in ["us", "fr"]:
            yield JsonRequest(
                f"https://czqk28jt.apicdn.sanity.io/v1/graphql/prod_plk_{country}/default",
                data={
                    "query": """query AllRestaurants {
                        allRestaurants(limit: -1, where: { environment: "prod", status: "Open" }) {
                            check_date: _updatedAt
                            ref: _id
                            latitude
                            longitude
                            addr_full: name
                            address: physicalAddress {
                                address1
                                address2
                                city
                                state: stateProvinceShort
                                postalCode
                                country
                            }
                            phone: phoneNumber
                            hasDelivery
                            hasDineIn
                            hasTakeOut
                            hasDriveThru
                            driveThruLaneType
                            hasPlayground
                            playgroundType
                            hasParking
                            hasWifi
                            isHalal
                            operator: franchiseGroupName
                            diningRoomHours {
                                MoOpen: monOpen
                                MoClose: monClose
                                TuOpen: tueOpen
                                TuClose: tueClose
                                WeOpen: wedOpen
                                WeClose: wedClose
                                ThOpen: thrOpen
                                ThClose: thrClose
                                FrOpen: friOpen
                                FrClose: friClose
                                SaOpen: satOpen
                                SaClose: satClose
                                SuOpen: sunOpen
                                SuClose: sunClose
                            }
                        }
                    }
                    """
                },
            )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["data"]["allRestaurants"]:
            if "Partner" in location.get("addr_full", "").title():  # Not a Popeyes branded location
                continue
            item = DictParser.parse(location)
            item["website"] = urljoin("https://www.popeyes.com/store-locator/store/", item["ref"])
            item["extras"]["check_date"] = location["check_date"]
            item["operator"] = location["operator"]
            item["addr_full"] = location["addr_full"]
            item["street_address"] = merge_address_lines(
                [location["address"]["address1"], location["address"]["address2"]]
            )
            apply_yes_no(Extras.DELIVERY, item, location["hasDelivery"])
            apply_yes_no(Extras.INDOOR_SEATING, item, location["hasDineIn"])
            apply_yes_no(Extras.TAKEAWAY, item, location["hasTakeOut"])
            apply_yes_no(Extras.DRIVE_THROUGH, item, location["hasDriveThru"])
            apply_yes_no(Extras.WIFI, item, location["hasWifi"])
            apply_yes_no(Extras.HALAL, item, location["isHalal"])
            item["opening_hours"] = OpeningHours()
            for day in DAYS:
                item["opening_hours"].add_range(
                    day,
                    location["diningRoomHours"]["{}Open".format(day)],
                    location["diningRoomHours"]["{}Close".format(day)],
                    "%Y-%m-%d %H:%M:%S",
                )
            yield item
