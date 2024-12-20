from typing import Any

import scrapy
from scrapy import Spider
from scrapy.http import Response

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


# TODO: Hertz also owns Dollar and Thrifty (https://en.wikipedia.org/wiki/Hertz_Global_Holdings
#       check if below spider can be re-used for those brands.
class HertzSpider(Spider):
    name = "hertz"
    item_attributes = {"brand": "Hertz", "brand_wikidata": "Q1543874"}
    start_urls = ["https://api.hertz.com/rest/geography/country"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for country_data in response.json()["data"]["model"]:
            country_name = country_data["name"]
            country_code = country_data["value"]
            yield scrapy.Request(
                url="https://api.hertz.com/rest/geography/city/country/{}".format(country_code),
                callback=self.parse_city,
                cb_kwargs={"country_name": country_name, "country_code": country_code},
            )

    def parse_city(self, response, **kwargs):
        for city_info in response.json()["data"]["model"]:
            city_name = city_info["name"]
            yield scrapy.Request(
                url="https://api.hertz.com/rest/location/country/{}/city/{}".format(kwargs["country_code"], city_name),
                callback=self.parse_details,
            )

    def parse_details(self, response, **kwargs):
        for shop in response.json()["data"]["locations"]:
            item = DictParser.parse(shop)
            item["ref"] = shop["extendedOAGCode"]
            item["email"] = shop["loc_email"]
            item["website"] = "/".join(
                ["https://www.hertz.com/us/en/location", shop["country_name"], shop["city"], shop["extendedOAGCode"]]
            )
            item["street_address"] = shop.get("streetAddressLine1")
            if shop.get("streetAddressLine2", ""):
                item["addr_full"] = "".join(
                    [
                        shop.get("streetAddressLine1", ""),
                        shop.get("streetAddressLine2", ""),
                        shop.get("streetAddressLine3", ""),
                    ]
                )
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(ranges_string=shop["hours"])
            yield item
