import json
from typing import Any, AsyncIterator

from scrapy.http import JsonRequest, TextResponse

from locations.categories import Categories, Extras, Fuel, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.geo import city_locations
from locations.hours import OpeningHours
from locations.playwright_spider import PlaywrightSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS


class CaseysGeneralStoreUSSpider(PlaywrightSpider):
    name = "caseys_general_store_us"
    item_attributes = {"brand": "Casey's General Store", "brand_wikidata": "Q2940968"}
    requires_proxy = True
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS

    async def start(self) -> AsyncIterator[Any]:
        url = "https://www.caseys.com/api/graphql"

        for city in city_locations("US", 10000):
            payload = {
                "operationName": "GetStoresByFilters",
                "variables": {
                    "input": {"latitude": f"{city['latitude']}", "longitude": f"{city['longitude']}"},
                },
                "extensions": {"clientLibrary": {"name": "@apollo/client", "version": "4.2.3"}},
                "query": """query GetStoresByFilters($input: StoresByCoordinateInput!) {
              storesByCoordinate(input: $input) {
                store {
                  name
                  displayName
                  brand
                  address {
                    id
                    line1
                    city
                    stateAbbreviation
                    postalCode
                    phoneNumber
                  }
                  geoPoint {
                    latitude
                    longitude
                  }
                  amenities {
                    key
                    isEnabled
                  }
                  amenityGroups {
                    code
                    amenities {
                      code
                      value {
                        ... on BooleanAmenityValue {
                          value
                        }
                      }
                    }
                  }
                  locationUrl
                  hours {
                    type
                    hours {
                      dayOfWeek
                      blocks {
                        openDateTime
                        closeDateTime
                      }
                    }
                  }
                }
              }
            }""",
            }

            yield JsonRequest(url=url, data=payload)

    def parse(self, response: TextResponse, **kwargs):
        for location in json.loads(response.xpath("//pre//text()").get())["data"]["storesByCoordinate"]:
            location.update(location.pop("store"))
            item = DictParser.parse(location)
            item["ref"] = item.pop("name")
            item["branch"] = location["displayName"]
            item["name"] = location["brand"]
            item["website"] = response.urljoin(location["locationUrl"])
            item["phone"] = location["address"]["phoneNumber"]
            item["state"] = location["address"]["stateAbbreviation"]

            depts = self.parse_departments(location["amenityGroups"])
            amenities = [amenity["key"] if amenity["isEnabled"] else None for amenity in location["amenities"]]
            hours = {h["type"]: self.parse_opening_hours(h["hours"]) for h in location["hours"]}

            if depts.get("fuel") and location["brand"] == "Casey's":
                fuel = item.deepcopy()
                fuel["ref"] = "{}_fuel".format(item["ref"])
                if "PUMPHOURS" in hours:
                    fuel["opening_hours"] = hours["PUMPHOURS"]
                if "has_24hourpayatpump" in depts["fuel"]:
                    fuel["opening_hours"] = "24/7"
                apply_yes_no(Fuel.DIESEL, fuel, "has_diesel" in depts["fuel"])
                apply_yes_no(Fuel.KEROSENE, fuel, "has_kerosene" in depts["fuel"])
                apply_yes_no(Fuel.OCTANE_88, fuel, "has_unleaded_88" in depts["fuel"])
                apply_yes_no(Extras.CAR_WASH, fuel, "carwash" in amenities)

                # has_def/DEF
                # has_flex_fuel/Flex fuel
                # has_midgrade/Midgrade
                # has_midgrade_no_ethanol/Midgrade no ethanol
                # has_premium/Premium
                # has_premium_diesel/Premium diesel
                # has_premium_no_ethanol/Premium no ethanol
                # has_racing_fuel/Racing fuel
                # has_red_dyed_diesel/Red dyed diesel
                # has_regular/Regular

                apply_category(Categories.FUEL_STATION, fuel)
                yield fuel

            if depts.get("store"):
                store = item.deepcopy()
                store["ref"] = "{}_store".format(item["ref"])
                if "STOREOPEN" in hours:
                    store["opening_hours"] = hours["STOREOPEN"]
                if "has_24_hours" in depts["store"]:
                    store["opening_hours"] = "24/7"
                apply_yes_no("sells:alcohol", store, "has_alcohol" in depts["store"])
                apply_yes_no(Extras.ATM, store, "has_atm" in depts["store"])

                apply_category(Categories.SHOP_CONVENIENCE, store)
                yield store

    def parse_departments(self, amenity_groups: list[dict]) -> dict:
        result = {}
        for group in amenity_groups:
            result[group["code"]] = set()
            for amenity in group["amenities"]:
                if amenity["value"]["value"] is True:
                    result[group["code"]].add(amenity["code"])

        return result

    def parse_opening_hours(self, hours: list[dict]) -> OpeningHours:
        oh = OpeningHours()
        for rule in hours:
            for times in rule["blocks"]:
                oh.add_range(rule["dayOfWeek"], times["openDateTime"], times["closeDateTime"], "%Y-%m-%dT%H:%M:%SZ")
        return oh
