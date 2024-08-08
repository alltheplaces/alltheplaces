import geonamescache
import scrapy

from locations.categories import Categories, Extras, apply_yes_no
from locations.dict_parser import DictParser
from locations.geo import city_locations, point_locations
from locations.hours import DAYS_EN, OpeningHours

BURGER_KING_SHARED_ATTRIBUTES = {
    "brand": "Burger King",
    "brand_wikidata": "Q177054",
    "extras": Categories.FAST_FOOD.value,
}


class BurgerKingSpider(scrapy.Spider):
    name = "burger_king"
    item_attributes = BURGER_KING_SHARED_ATTRIBUTES
    download_delay = 2.0
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def make_request(self, lat, lon, country_code, search_radius, result_limit, url):
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
            url=url,
            data=body,
            headers={"x-ui-language": "en", "x-ui-region": country_code},
            cb_kwargs=dict(country_code=country_code),
        )

    def make_city_request(self, city_name, country_code, search_radius, result_limit, url):
        for city in city_locations(country_code):
            if city.get("name", "").lower() == city_name.lower() and city.get("latitude") and city.get("longitude"):
                self.logger.info("Making city request for %s, %s", country_code, city_name)
                return self.make_request(
                    city["latitude"],
                    city["longitude"],
                    country_code,
                    search_radius,
                    result_limit,
                    url,
                )
        raise Exception("Bogus City: " + city_name)

    def get_eu_capitals(self):
        gc = geonamescache.GeonamesCache()
        return [(c["iso"], c["capital"]) for c in gc.get_countries().values() if c["continentcode"] == "EU"]

    def start_requests(self):
        # TODO: DK, IE, MX, SE at the least do not follow this API.
        eu_endpoint = "https://euc1-prod-bk.rbictg.com/graphql"
        us_endpoint = "https://use1-prod-bk.rbictg.com/graphql"

        # Europe
        for country_code, city_name in self.get_eu_capitals():
            # Currently we have data for AT, CH, CZ, DE, ES, GB, NL, PL, PT, RO in eu_endpoint (2023-11-22)
            if country_code in ["AT", "CH", "CZ", "DE", "ES", "GB", "NL", "PL", "PT", "RO"]:
                yield self.make_city_request(city_name, country_code, 1000000, 20000, eu_endpoint)

        # Canada, New Zealand
        for country_code, city_name in [("CA", "Calgary"), ("CA", "Toronto"), ("NZ", "Auckland")]:
            yield self.make_city_request(city_name, country_code, 1000000, 20000, us_endpoint)

        # USA
        # So many stores in the US that we need to be kind to the BK back end.
        for lat, lon in point_locations("us_centroids_100mile_radius.csv"):
            yield self.make_request(lat, lon, "US", 128000, 20000, us_endpoint)

    store_locator_templates = {
        "AT": "https://www.burgerking.at/store-locator/store/{}",
        "CA": "https://www.burgerking.ca/store-locator/store/{}",
        "CH": "https://www.burger-king.ch/store-locator/store/{}",
        "DE": "https://www.burgerking.de/store-locator/store/{}",
        "GB": "https://www.burgerking.co.uk/store-locator/store/{}",
        "NZ": "https://www.burgerking.co.nz/store-locator/store/{}",
        "NL": "https://www.burgerking.nl/store-locator/store/{}",
        "PL": "https://burgerking.pl/store-locator/store/{}",
        "US": "https://www.bk.com/store-locator/store/{}",
    }

    def parse(self, response, country_code):
        for row in response.json()[0]["data"]["restaurants"]["nodes"]:
            row.update(row.pop("physicalAddress"))
            item = DictParser.parse(row)
            item["name"] = "Burger King"
            item["country"] = country_code
            item["addr_full"] = None
            item["website"] = self.store_locator_templates.get(country_code, "").format(row["_id"]) or None
            item["operator"] = row.get("franchiseGroupName")
            apply_yes_no(Extras.WIFI, item, row.get("hasWifi"), True)
            apply_yes_no(Extras.DRIVE_THROUGH, item, row.get("hasDriveThru"), True)
            apply_yes_no(Extras.DELIVERY, item, row.get("hasDelivery"), True)
            apply_yes_no(Extras.TAKEAWAY, item, row.get("hasTakeOut"), True)
            apply_yes_no(Extras.HALAL, item, row.get("isHalal"), True)
            self.parse_hours(item, row)
            yield item

    def parse_hours(self, item, row):
        """
        hours format:
        "diningRoomHours": {
            "friClose": "04:00:00",
            "friOpen": "11:00:00",
            "monClose": "23:00:00",
            "monOpen": "11:00:00",
            "satClose": "04:00:00",
            "satOpen": "11:00:00",
            "sunClose": "23:00:00",
            "sunOpen": "11:00:00",
            "thrClose": "23:00:00",
            "thrOpen": "11:00:00",
            "tueClose": "23:00:00",
            "tueOpen": "11:00:00",
            "wedClose": "04:00:00",
            "wedOpen": "11:00:00",
            "__typename": "OperatingHours"
            }
        """
        # TODO: parse driveThruHours
        if hours := row.get("diningRoomHours"):
            try:
                oh = OpeningHours()
                for day in ["mon", "tue", "wed", "thr", "fri", "sat", "sun"]:
                    if hours.get(f"{day}Open"):
                        oh.add_range(
                            DAYS_EN.get(day.title()), hours.get(f"{day}Open"), hours.get(f"{day}Close"), "%H:%M:%S"
                        )
                item["opening_hours"] = oh.as_opening_hours()
            except Exception as e:
                self.logger.warning("Failed to parse hours for %s: %s", item["ref"], e)
