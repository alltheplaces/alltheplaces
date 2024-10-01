import geonamescache
import scrapy

from locations.categories import Categories, Extras, apply_yes_no
from locations.dict_parser import DictParser
from locations.geo import city_locations, country_iseadgg_centroids
from locations.hours import DAYS_EN, OpeningHours
from locations.pipelines.address_clean_up import clean_address

BURGER_KING_SHARED_ATTRIBUTES = {
    "brand": "Burger King",
    "brand_wikidata": "Q177054",
    "extras": Categories.FAST_FOOD.value,
}


class BurgerKingSpider(scrapy.Spider):
    download_timeout = 30
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
                    "  hasBreakfast\n"
                    "  hasDelivery\n"
                    "  hasDriveThru\n"
                    "  hasPlayground\n"
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
        ae_endpoint = "https://www.burgerking.ae/api/whitelabel"
        eu_endpoint = "https://euc1-prod-bk.rbictg.com/graphql"
        gb_endpoint = "https://www.burgerking.co.uk/api/whitelabel"
        nz_endpoint = "https://www.burgerking.co.nz/api/whitelabel"
        sa_endpoint = "https://www.burgerking.com.sa/api/whitelabel"
        us_endpoint = "https://use1-prod-bk.rbictg.com/graphql"
        za_endpoint = "https://www.burgerking.co.za/api/whitelabel"

        # UAE
        for country_code, city_name in [("AE", "Dubai")]:
            yield self.make_city_request(city_name, country_code, 1000000, 20000, ae_endpoint)

        # Europe
        for country_code, city_name in self.get_eu_capitals():
            # Currently we have data for AT, CH, CZ, DE, ES, GB, NL, PL, PT, RO in eu_endpoint (2024-09-26)
            if country_code in ["AT", "CH", "CZ", "DE", "ES", "NL", "PL", "PT", "RO"]:
                yield self.make_city_request(city_name, country_code, 1000000, 20000, eu_endpoint)

        # Canada
        for country_code, city_name in [("CA", "Calgary"), ("CA", "Toronto")]:
            yield self.make_city_request(city_name, country_code, 1000000, 20000, us_endpoint)

        # New Zealand
        for country_code, city_name in [("NZ", "Auckland")]:
            yield self.make_city_request(city_name, country_code, 1000000, 20000, nz_endpoint)

        # Saudi Arabia
        for country_code, city_name in [("SA", "Jeddah")]:
            yield self.make_city_request(city_name, country_code, 1000000, 20000, sa_endpoint)

        # South Africa
        for country_code, city_name in [("ZA", "Johannesburg")]:
            yield self.make_city_request(city_name, country_code, 1000000, 20000, za_endpoint)

        # United Kingdom
        for country_code, city_name in [("GB", "London")]:
            yield self.make_city_request(city_name, country_code, 1000000, 20000, gb_endpoint)

        # USA
        # So many stores in the US that we need to be kind to the BK back end.
        for lat, lon in country_iseadgg_centroids(["US"], 158):
            yield self.make_request(lat, lon, "US", 128000, 20000, us_endpoint)

    store_locator_templates = {
        "AT": "https://www.burgerking.at/store-locator/store/{}",
        "CA": "https://www.burgerking.ca/store-locator/store/{}",
        "CH": "https://www.burger-king.ch/store-locator/store/{}",
        "CZ": "https://burgerking.cz/store-locator/store/{}",
        "DE": "https://www.burgerking.de/store-locator/store/{}",
        "GB": "https://www.burgerking.co.uk/store-locator/store/{}",
        "NL": "https://www.burgerking.nl/store-locator/store/{}",
        "NZ": "https://www.burgerking.co.nz/store-locator/store/{}",
        "PL": "https://burgerking.pl/store-locator/store/{}",
        "PT": "https://www.burgerking.pt/store-locator/store/{}",
        "RO": "https://burgerking.ro/store-locator/store/{}",
        "SA": "https://www.burgerking.com.sa/ar/store-locator/store/{}",
        "US": "https://www.bk.com/store-locator/store/{}",
        "ZA": "https://www.burgerking.co.za/store-locator/store/{}",
    }

    def parse(self, response, country_code):
        for location in response.json()[0]["data"]["restaurants"]["nodes"]:
            location.update(location.pop("physicalAddress"))
            item = DictParser.parse(location)
            item["branch"] = item.pop("name")
            item["country"] = country_code
            item["addr_full"] = clean_address(
                [
                    location.get("address1"),
                    location.get("address2"),
                    location.get("city"),
                    location.get("stateProvince"),
                    location.get("postalCode"),
                ]
            )

            item["website"] = self.store_locator_templates.get(country_code, "").format(location["_id"]) or None
            if country_code == "SA" and item["website"] is not None:
                item["extras"]["website:ar"] = item["website"]
                item["extras"]["website:en"] = item["website"].replace(".com.sa/ar/store", ".com.sa/en/store")

            item["operator"] = location.get("franchiseGroupName")

            apply_yes_no(Extras.WIFI, item, location.get("hasWifi"))
            apply_yes_no(Extras.DRIVE_THROUGH, item, location.get("hasDriveThru"), False)
            apply_yes_no(Extras.DELIVERY, item, location.get("hasDelivery"), False)
            apply_yes_no(Extras.TAKEAWAY, item, location.get("hasTakeOut"), False)
            apply_yes_no(Extras.HALAL, item, location.get("isHalal"), True)
            apply_yes_no(Extras.KIDS_AREA, item, location.get("hasPlayground"), False)
            apply_yes_no(Extras.BREAKFAST, item, location.get("hasBreakfast"), False)

            if hours := location.get("diningRoomHours"):
                item["opening_hours"] = self.parse_opening_hours(hours)
            if location.get("hasDriveThru"):
                if drive_through_hours := self.parse_opening_hours(location.get("driveThruHours")).as_opening_hours():
                    item["extras"]["opening_hours:drive_through"] = drive_through_hours
            if location.get("hasDelivery"):
                if drive_through_hours := self.parse_opening_hours(location.get("deliveryHours")).as_opening_hours():
                    item["extras"]["opening_hours:delivery"] = drive_through_hours

            yield item

    def parse_opening_hours(self, hours: dict) -> OpeningHours:
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
        if hours is None:
            return None
        try:
            oh = OpeningHours()
            for day in ["mon", "tue", "wed", "thr", "fri", "sat", "sun"]:
                if hours.get(f"{day}Open"):
                    oh.add_range(
                        DAYS_EN.get(day.title()), hours.get(f"{day}Open"), hours.get(f"{day}Close"), "%H:%M:%S"
                    )
            return oh
        except Exception as e:
            self.logger.warning("Failed to parse hours for %s: %s", item["ref"], e)
            return None
