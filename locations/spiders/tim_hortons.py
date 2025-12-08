from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Extras, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import merge_address_lines


class TimHortonsSpider(Spider):
    name = "tim_hortons"
    item_attributes = {"brand": "Tim Hortons", "brand_wikidata": "Q175106"}
    allowed_domains = ["czqk28jt.apicdn.sanity.io"]

    def start_requests(self):
        yield JsonRequest(
            url="https://czqk28jt.apicdn.sanity.io/v1/graphql/prod_th_us/default",
            data={
                "query": """
                 query AllRestaurants($filter: RestaurantFilter, $limit: Int) {
                    allRestaurants(where: $filter, limit: $limit) {
                        check_date: _updatedAt
                        hasDelivery
                        hasDineIn
                        hasTakeOut
                        hasDriveThru
                        hasCurbside
                        hasCatering
                        hasTableService
                        hasBreakfast
                        ref: number
                        phoneNumber
                        address: physicalAddress {
                            address1
                            address2
                            city
                            postalCode
                            state: stateProvinceShort
                            country
                        }
                        restaurantImage {
                            asset {
                                url
                            }
                        }
                        vatNumber
                        latitude
                        longitude
                        driveThruLaneType
                        hasPlayground
                        hasParking
                        hasWifi
                        hasMobileOrdering
                        isHalal
                        operator: franchiseGroupName
                        operator_id: franchiseGroupId
                        email
                        isDarkKitchen
                        diningRoomHours {
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
                            sunOpen
                            sunClose
                        }
                    }
                }""",
                "variables": {"filter": {"status": "Open", "environment": "prod"}, "limit": 10000},
            },
        )

    def parse(self, response):
        locations = response.json()["data"]["allRestaurants"]
        for location in locations:
            if location["isDarkKitchen"]:
                continue  # No OSM tagging yet

            item = DictParser.parse(location)
            item["street_address"] = merge_address_lines(
                [location["address"]["address1"], location["address"]["address2"]]
            )
            item["image"] = (location["restaurantImage"] or {}).get("asset", {}).get("url")
            item["extras"]["check_date"] = location["check_date"]
            if location["operator_id"] is not None:
                item["operator"] = location["operator"]
                item["extras"]["operator:ref"] = str(location["operator_id"])

            if isinstance(item["email"], list):
                item["email"] = ";".join(item["email"])

            apply_yes_no(Extras.TAKEAWAY, item, location["hasTakeOut"])
            apply_yes_no(Extras.DRIVE_THROUGH, item, location["hasDriveThru"], False)
            apply_yes_no(Extras.INDOOR_SEATING, item, location["hasDineIn"], False)
            apply_yes_no(Extras.DELIVERY, item, location["hasDelivery"], False)
            apply_yes_no(Extras.WIFI, item, location["hasWifi"], False)
            apply_yes_no(Extras.HALAL, item, location["isHalal"])

            item["opening_hours"] = OpeningHours()
            for day in ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]:
                if not location["diningRoomHours"].get(f"{day}Open") or not location["diningRoomHours"].get(
                    f"{day}Close"
                ):
                    continue
                open_time = location["diningRoomHours"][f"{day}Open"].split(" ", 1)[1]
                close_time = location["diningRoomHours"][f"{day}Close"].split(" ", 1)[1]
                item["opening_hours"].add_range(day.title(), open_time, close_time, "%H:%M:%S")

            yield item
