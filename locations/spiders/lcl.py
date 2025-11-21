from typing import AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.geo import city_locations


class LclSpider(Spider):
    name = "lcl"
    item_attributes = {"brand": "LCL", "brand_wikidata": "Q779722"}

    async def start(self) -> AsyncIterator[JsonRequest]:
        for city in city_locations("FR", 15000):
            yield JsonRequest(
                url="https://www.lcl.fr/api/graphql",
                data={
                    "operationName": "agencyQuery",
                    "variables": {"query": city["name"]},
                    "query": "query agencyQuery($query: String, $latitude: Float, $longitude: Float, $hasVault: Boolean, $isOpenSaturday: Boolean, $isPrivateBank: Boolean, $isProBank: Boolean) {\n  agencies(query: $query, latitude: $latitude, longitude: $longitude, hasVault: $hasVault, isOpenSaturday: $isOpenSaturday, isPrivateBank: $isPrivateBank, isProBank: $isProBank) {\n    number\n    agencies {\n      id\n      name\n      address\n      postalCode\n      town\n      country\n      phoneNumber\n      fax\n      agencyType\n      hasVault\n      latitude\n      longitude\n      distance\n      timezone\n      hours {\n        monday {\n          isOpen\n          openingHours {\n            amOpen\n            amClose\n            pmOpen\n            pmClose\n            __typename\n          }\n          __typename\n        }\n        tuesday {\n          isOpen\n          openingHours {\n            amOpen\n            amClose\n            pmOpen\n            pmClose\n            __typename\n          }\n          __typename\n        }\n        wednesday {\n          isOpen\n          openingHours {\n            amOpen\n            amClose\n            pmOpen\n            pmClose\n            __typename\n          }\n          __typename\n        }\n        thursday {\n          isOpen\n          openingHours {\n            amOpen\n            amClose\n            pmOpen\n            pmClose\n            __typename\n          }\n          __typename\n        }\n        friday {\n          isOpen\n          openingHours {\n            amOpen\n            amClose\n            pmOpen\n            pmClose\n            __typename\n          }\n          __typename\n        }\n        saturday {\n          isOpen\n          openingHours {\n            amOpen\n            amClose\n            pmOpen\n            pmClose\n            __typename\n          }\n          __typename\n        }\n        sunday {\n          isOpen\n          openingHours {\n            amOpen\n            amClose\n            pmOpen\n            pmClose\n            __typename\n          }\n          __typename\n        }\n        __typename\n      }\n      closedDates {\n        begin\n        end\n        __typename\n      }\n      communicationArea\n      __typename\n    }\n    __typename\n  }\n}\n",
                },
            )

    def parse(self, response):
        country = {"Saint-Martin": "MF", "Saint-Barthélemy": "BL"}
        for location in response.json()["data"]["agencies"].get("agencies"):
            item = DictParser.parse(location)
            item["street_address"] = item.pop("addr_full")
            if location["country"] in country:
                item["country"] = country[location["country"]]
            item["website"] = "https://www.lcl.fr/agence-banque/{}-{}".format(
                item["ref"], item["name"].replace(" ", "-")
            )
            apply_category(Categories.BANK, item)
            yield item
