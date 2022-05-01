# -*- coding: utf-8 -*-
import scrapy

from locations.items import GeojsonPointItem


class BurgerKingUKSpider(scrapy.Spider):
    name = "burgerkinguk"
    item_attributes = {"brand": "Burger King", "brand_wikidata": "Q177054"}

    def make_request(self, lat, lon):
        body = [
            {
                "operationName": "GetRestaurants",
                "variables": {
                    "input": {
                        "filter": "NEARBY",
                        "coordinates": {
                            "userLat": lat,
                            "userLng": lon,
                            "searchRadius": 1000000,
                        },
                        "first": 20000,
                    }
                },
                "query": (
                    "query GetRestaurants($input: RestaurantsInput) {\n"
                    "  restaurants(input: $input) {\n"
                    "    pageInfo {\n"
                    "      hasNextPage\n"
                    "      endCursor\n"
                    "      __typename\n"
                    "    }\n"
                    "    totalCount\n"
                    "    nodes {\n"
                    "      ...RestaurantNodeFragment\n"
                    "      __typename\n"
                    "    }\n"
                    "    __typename\n"
                    "  }\n"
                    "}\n"
                    "\n"
                    "fragment RestaurantNodeFragment on RestaurantNode {\n"
                    "  _id\n"
                    "  storeId\n"
                    "  curbsideHours {\n"
                    "    ...OperatingHoursFragment\n"
                    "    __typename\n"
                    "  }\n"
                    "  deliveryHours {\n"
                    "    ...OperatingHoursFragment\n"
                    "    __typename\n"
                    "  }\n"
                    "  diningRoomHours {\n"
                    "    ...OperatingHoursFragment\n"
                    "    __typename\n"
                    "  }\n"
                    "  driveThruHours {\n"
                    "    ...OperatingHoursFragment\n"
                    "    __typename\n"
                    "  }\n"
                    "  email\n"
                    "  franchiseGroupName\n"
                    "  hasDelivery\n"
                    "  hasDriveThru\n"
                    "  hasTakeOut\n"
                    "  hasWifi\n"
                    "  id\n"
                    "  isDarkKitchen\n"
                    "  isHalal\n"
                    "  latitude\n"
                    "  longitude\n"
                    "  name\n"
                    "  phoneNumber\n"
                    "  physicalAddress {\n"
                    "    address1\n"
                    "    address2\n"
                    "    city\n"
                    "    country\n"
                    "    postalCode\n"
                    "    stateProvince\n"
                    "    stateProvinceShort\n"
                    "    __typename\n"
                    "  }\n"
                    "  __typename\n"
                    "}\n"
                    "\n"
                    "fragment OperatingHoursFragment on OperatingHours {\n"
                    "  friClose\n"
                    "  friOpen\n"
                    "  monClose\n"
                    "  monOpen\n"
                    "  satClose\n"
                    "  satOpen\n"
                    "  sunClose\n"
                    "  sunOpen\n"
                    "  thrClose\n"
                    "  thrOpen\n"
                    "  tueClose\n"
                    "  tueOpen\n"
                    "  wedClose\n"
                    "  wedOpen\n"
                    "  __typename\n"
                    "}\n"
                ),
            }
        ]
        return scrapy.http.JsonRequest(
            "https://use1-prod-bk.rbictg.com/graphql",
            data=body,
            headers={"x-ui-language": "en", "x-ui-region": "GB"},
        )

    def start_requests(self):
        yield self.make_request(52.905499, -1.536478)

    def parse(self, response):
        data = response.json()
        for row in data[0]["data"]["restaurants"]["nodes"]:
            properties = {
                "website": f'https://www.burgerking.co.uk/store-locator/store/{row["_id"]}',
                "lat": row["latitude"],
                "lon": row["longitude"],
                "ref": row["storeId"],
                "name": row["name"],
                "phone": row["phoneNumber"],
                "street_address": row["physicalAddress"]["address1"],
                "city": row["physicalAddress"]["city"],
                "state": row["physicalAddress"]["stateProvince"],
                "postcode": row["physicalAddress"]["postalCode"],
                "country": "GB",
                "addr_full": ", ".join(
                    filter(
                        None,
                        (
                            row["physicalAddress"]["address1"],
                            row["physicalAddress"]["address2"],
                            row["physicalAddress"]["city"],
                            row["physicalAddress"]["postalCode"],
                            "United Kingdom",
                        ),
                    )
                ),
                "extras": {
                    "operator": row["franchiseGroupName"],
                    "internet_access": "wlan" if row["hasWifi"] == True else "no",
                    "diet:halal": "yes" if row["isHalal"] == True else "no",
                    "delivery": "yes" if row["hasDelivery"] == True else "no",
                    "drive_through": "yes" if row["hasDriveThru"] == True else "no",
                    "takeaway": "yes" if row["hasTakeOut"] == True else "no",
                    "email": row["email"],
                },
            }
            yield GeojsonPointItem(**properties)
