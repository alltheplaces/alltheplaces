from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Extras, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class TimHortonsSpider(Spider):
    name = "tim_hortons"
    item_attributes = {"brand": "Tim Hortons", "brand_wikidata": "Q175106"}
    allowed_domains = ["czqk28jt.apicdn.sanity.io"]

    def start_requests(self):
        graphql_query = "query GetRestaurants($filter:RestaurantFilter,$limit:Int){allRestaurants(where:$filter,limit:$limit){...RestaurantFragment}} fragment RestaurantFragment on Restaurant{environment diningRoomHours{...HoursFragment} email hasBreakfast hasBurgersForBreakfast hasCurbside hasDineIn hasCatering hasDelivery hasDriveThru hasTableService hasMobileOrdering hasParking hasPlayground hasTakeOut hasWifi hasLoyalty latitude longitude  name number phoneNumber physicalAddress{address1 address2 city country postalCode stateProvince} status} fragment HoursFragment on HoursOfOperation{friClose friOpen monClose monOpen satClose satOpen sunClose sunOpen thrClose thrOpen tueClose tueOpen wedClose wedOpen}"
        data = {
            "query": graphql_query,
            "variables": {"filter": {"status": "Open", "environment": "prod"}, "limit": 10000},
        }
        yield JsonRequest(url="https://czqk28jt.apicdn.sanity.io/v1/graphql/prod_th_us/default", data=data)

    def parse(self, response):
        locations = response.json()["data"]["allRestaurants"]
        for location in locations:
            item = DictParser.parse(location)
            item["ref"] = location["number"]

            if isinstance(item["email"], list):
                item["email"] = ",".join(item["email"])

            apply_yes_no(Extras.TAKEAWAY, item, location["hasTakeOut"] or location["hasDriveThru"], False)
            apply_yes_no(Extras.DRIVE_THROUGH, item, location["hasDriveThru"], False)
            apply_yes_no(Extras.INDOOR_SEATING, item, location["hasDineIn"], False)
            apply_yes_no(Extras.DELIVERY, item, location["hasDelivery"], False)
            apply_yes_no(Extras.WIFI, item, location["hasWifi"], False)

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
