import scrapy

from locations.dict_parser import DictParser
from locations.geo import city_locations, point_locations


class BurgerKingSpider(scrapy.Spider):
    name = "burgerking"
    item_attributes = {"brand": "Burger King", "brand_wikidata": "Q177054"}
    download_delay = 2.0
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def make_request(self, lat, lon, country_code, search_radius, result_limit):
        body = [
            {
                "operationName": "GetRestaurants",
                "variables": {
                    "input": {
                        "filter": "NEARBY",
                        "coordinates": {
                            "userLat": float(lat),
                            "userLng": float(lon),
                            "searchRadius": search_radius,
                        },
                        "first": result_limit,
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
            headers={"x-ui-language": "en", "x-ui-region": country_code},
            cb_kwargs=dict(country_code=country_code),
        )

    def make_city_request(self, city_name, country_code, search_radius, result_limit):
        for city in city_locations(country_code):
            if city["name"].lower() == city_name.lower():
                return self.make_request(
                    city["latitude"],
                    city["longitude"],
                    country_code,
                    search_radius,
                    result_limit,
                )
        raise Exception("Bogus City: " + city_name)

    def start_requests(self):
        # TODO: DK, IE, MX, at the least do not follow this API.

        # TODO: https://www.burgerking.nl/kingfinder
        # TODO: has an interface for central european and nordic countries

        yield self.make_city_request("Calgary", "CA", 1000000, 20000)
        yield self.make_city_request("Toronto", "CA", 1000000, 20000)
        yield self.make_city_request("Frankfurt am Main", "DE", 1000000, 20000)
        yield self.make_city_request("Leeds", "GB", 1000000, 20000)
        yield self.make_city_request("Auckland", "NZ", 1000000, 20000)
        # So many stores in the US that we need to be kind to the BK back end.
        for lat, lon in point_locations("us_centroids_100mile_radius.csv"):
            yield self.make_request(lat, lon, "US", 128000, 20000)

    store_locator_templates = {
        "CA": "https://www.burgerking.ca/store-locator/store/{}",
        "DE": "https://www.burgerking.de/store-locator/store/{}",
        "GB": "https://www.burgerking.co.uk/store-locator/store/{}",
        "NZ": "https://www.burgerking.co.nz/store-locator/store/{}",
        "US": "https://www.bk.com/store-locator/store/{}",
    }

    def parse(self, response, country_code):
        for row in response.json()[0]["data"]["restaurants"]["nodes"]:
            row.update(row.pop("physicalAddress"))
            item = DictParser.parse(row)
            item["name"] = "Burger King"
            item["country"] = country_code
            item["addr_full"] = None
            item["website"] = self.store_locator_templates[country_code].format(row["_id"])
            item["operator"] = row["franchiseGroupName"]
            item["extras"] = {
                "internet_access": "wlan" if row["hasWifi"] is True else "no",
                "diet:halal": "yes" if row["isHalal"] is True else "no",
                "delivery": "yes" if row["hasDelivery"] is True else "no",
                "drive_through": "yes" if row["hasDriveThru"] is True else "no",
                "takeaway": "yes" if row["hasTakeOut"] is True else "no",
            }
            # TODO: somebody could decode the opening hours from the BK JSON.
            yield item
