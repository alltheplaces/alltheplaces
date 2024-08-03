from copy import deepcopy
from typing import Any, Iterable

from scrapy import Request, Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours, sanitise_day


class HEBUSSpider(Spider):
    name = "h_e_b_us"
    item_attributes = {"brand": "H-E-B", "brand_wikidata": "Q830621"}
    proxy_required = True

    def start_requests(self) -> Iterable[Request]:
        graphql_query = {
            "query": """
                query StoreDetailsSearch($address: String!, $radius: Int!, $size: Int!) {
                    searchStoresByAddress(
                        address: $address
                        radiusMiles: $radius
                        size: $size
                    ) {
                        stores {
                            store {
                                storeNumber
                                name
                                address{
                                    streetAddress
                                    locality
                                    region
                                    postalCode
                                    country
                                }
                                latitude
                                longitude
                                storeHours{
                                    day
                                    opens
                                    closes
                                }
                                phoneNumber
                                hasPharmacy: pharmacyStore
                                areas{
                                    id
                                    name
                                    customerFriendlyName
                                    areaHours{
                                        day
                                        opens
                                        closes
                                    }
                                    phoneNumber
                                }
                            }
                        }
                    }
                }
                """,
            "operationName": "StoreDetailsSearch",
            "variables": {"address": "", "radius": 10000, "size": 5000},
        }
        yield JsonRequest(url="https://www.heb.com/graphql", data=graphql_query)

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["data"]["searchStoresByAddress"]["stores"]:
            item = DictParser.parse(location["store"])
            item["ref"] = str(item["ref"])
            item[
                "website"
            ] = f'https://www.heb.com/heb-store/{item["country"]}/{item["state"]}/{item["city"]}/{item["name"]}-{item["ref"]}'.lower().replace(
                " ", "-"
            )

            location_name = item["name"].lower()
            if location["store"]["hasPharmacy"] and "pharmacy" not in location_name:
                # pharmacy adjacently located to the H-E-B supermarket
                pharmacy = deepcopy(item)
                pharmacy["name"] = pharmacy["brand"] = "H-E-B Pharmacy"
                pharmacy_info = {}
                for area in location["store"]["areas"]:
                    if area["name"] == "Pharmacy":
                        pharmacy_info = area
                        break
                pharmacy["ref"] += "-pharmacy"
                pharmacy["opening_hours"] = self.parse_opening_hours(pharmacy_info["areaHours"])
                pharmacy["phone"] = pharmacy_info["phoneNumber"]
                apply_category(Categories.PHARMACY, pharmacy)
                yield pharmacy
            if "pharmacy" in location_name:
                item["brand"] = "H-E-B Pharmacy"
                apply_category(Categories.PHARMACY, item)
            elif "plus!" in location_name:
                item["brand"] = "H-E-B plus!"
                apply_category(Categories.SHOP_SUPERMARKET, item)
            else:
                apply_category(Categories.SHOP_SUPERMARKET, item)

            # Other category locations like fuel stations, car wash and convenience shops detail are available on
            # the following page: https://www.heb.com/static-page/heb-convenience-stores

            item["opening_hours"] = self.parse_opening_hours(location["store"]["storeHours"])
            yield item

    def parse_opening_hours(self, rules: list[dict]) -> OpeningHours:
        opening_hours = OpeningHours()
        for rule in rules:
            if day := sanitise_day(rule["day"]):
                opening_hours.add_range(day, rule["opens"], rule["closes"])
        return opening_hours
