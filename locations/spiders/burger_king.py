from typing import Any, AsyncIterator

import geonamescache
from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.geo import city_locations, country_iseadgg_centroids
from locations.hours import DAYS_EN, OpeningHours
from locations.pipelines.address_clean_up import clean_address

BURGER_KING_SHARED_ATTRIBUTES = {
    "brand": "Burger King",
    "brand_wikidata": "Q177054",
}


class BurgerKingSpider(Spider):
    name = "burger_king"
    item_attributes = BURGER_KING_SHARED_ATTRIBUTES
    custom_settings = {"ROBOTSTXT_OBEY": False, "DOWNLOAD_DELAY": 2, "DOWNLOAD_TIMEOUT": 120}

    def make_request(
        self, lat: float | str, lon: float | str, country_code: str, search_radius: int, result_limit: int, url: str
    ) -> JsonRequest:
        body = {
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
            "query": """
                    query GetRestaurants($input: RestaurantsInput) {
                      restaurants(input: $input) {
                        pageInfo {
                          hasNextPage
                          endCursor
                          __typename
                        }
                        totalCount
                        nodes {
                          ...RestaurantNodeFragment
                          __typename
                        }
                        __typename
                      }
                    }

                    fragment RestaurantNodeFragment on RestaurantNode {
                      _id
                      storeId
                      curbsideHours {
                        ...OperatingHoursFragment
                        __typename
                      }
                      deliveryHours {
                        ...OperatingHoursFragment
                        __typename
                      }
                      diningRoomHours {
                        ...OperatingHoursFragment
                        __typename
                      }
                      driveThruHours {
                        ...OperatingHoursFragment
                        __typename
                      }
                      email
                      franchiseGroupName
                      hasBreakfast
                      hasDelivery
                      hasDriveThru
                      hasPlayground
                      hasTakeOut
                      hasWifi
                      isDarkKitchen
                      isHalal
                      latitude
                      longitude
                      name
                      phoneNumber
                      physicalAddress {
                        address1
                        address2
                        city
                        country
                        postalCode
                        stateProvince
                        stateProvinceShort
                        __typename
                      }
                      __typename
                    }

                    fragment OperatingHoursFragment on OperatingHours {
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
                      __typename
                    }
                """,
        }
        return JsonRequest(
            url=url,
            data=body,
            headers={"x-ui-language": "en", "x-ui-region": country_code},
            cb_kwargs=dict(country_code=country_code),
        )

    def make_city_request(self, city_name: str, country_code: str, search_radius: int, result_limit: int, url: str):
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

    async def start(self) -> AsyncIterator[JsonRequest]:
        ae_endpoint = "https://euc1-prod-bk-gateway.rbictg.com/graphql"
        eu_endpoint = "https://euc1-prod-bk.rbictg.com/graphql"
        gb_endpoint = "https://euc1-prod-bk.rbictg.com/graphql"
        nz_endpoint = "https://apse1-prod-bk-gateway.rbictg.com/graphql"
        sa_endpoint = "https://euc1-prod-bk-gateway.rbictg.com/graphql"
        us_endpoint = "https://use1-prod-bk-gateway.rbictg.com/graphql"
        za_endpoint = "https://euc1-prod-bk-gateway.rbictg.com/graphql"
        ie_endpoint = "https://euc1-prod-bk-gateway.rbictg.com/graphql"
        ar_cl_endpoint = "https://use2-prod-bk.rbictg.com/graphql"

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

        # Ireland
        for country_code, city_name in [("IE", "Dublin")]:
            yield self.make_city_request(city_name, country_code, 1000000, 20000, ie_endpoint)

        # Argentina
        for country_code, city_name in [("AR", "Córdoba")]:
            yield self.make_city_request(city_name, country_code, 1000000, 20000, ar_cl_endpoint)

        # Chile
        for country_code, city_name in [("CL", "Santiago")]:
            yield self.make_city_request(city_name, country_code, 1000000, 20000, ar_cl_endpoint)

        # USA
        # So many stores in the US that we need to be kind to the BK back end.
        for lat, lon in country_iseadgg_centroids(["US"], 158):
            yield self.make_request(lat, lon, "US", 128000, 20000, us_endpoint)

    store_locator_templates = {
        "AE": "https://www.burgerking.ae/ar/store-locator/store/{}",
        "AR": "https://burgerking.com.ar/es/store-locator/store/{}",
        "AT": "https://www.burgerking.at/de/store-locator/store/{}",
        "CA": "https://www.burgerking.ca/store-locator/store/{}",
        "CH": "https://www.burger-king.ch/de/store-locator/store/{}",
        "CL": "https://www.burgerking.cl/es/store-locator/store/{}",
        "CZ": "https://burgerking.cz/cs/store-locator/store/{}",
        "DE": "https://www.burgerking.de/store-locator/store/{}",
        "ES": "https://www.burgerking.es/es/store-locator/store/{}",
        "GB": "https://www.burgerking.co.uk/store-locator/store/{}",
        "IE": "https://burgerking.ie/store-locator/store/{}",
        "NL": "https://www.burgerking.nl/store-locator/store/{}",
        "NZ": "https://www.burgerking.co.nz/store-locator/store/{}",
        "PL": "https://burgerking.pl/pl/store-locator/store/{}",
        "PT": "https://www.burgerking.pt/pt/store-locator/store/{}",
        "RO": "https://burgerking.ro/ro/store-locator/store/{}",
        "SA": "https://www.burgerking.com.sa/ar/store-locator/store/{}",
        "US": "https://www.bk.com/store-locator/store/{}",
        "ZA": "https://www.burgerking.co.za/store-locator/store/{}",
    }

    def parse(self, response: Response, country_code: str) -> Any:
        restaurants = response.json().get("data", {}).get("restaurants") or {}
        for location in restaurants.get("nodes") or []:
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
            if country_code in ["CA", "US"]:
                item["website"] = item["website"].replace("restaurant_", "")
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

            apply_category(Categories.FAST_FOOD, item)

            yield item

    def parse_opening_hours(self, hours: dict) -> OpeningHours | None:
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
            self.logger.warning("Failed to parse hours: %s", e)
            return None
