from typing import Any, Iterable

import scrapy
from scrapy import Request
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.geo import city_locations
from locations.hours import OpeningHours
from locations.user_agents import BROWSER_DEFAULT


class WawaSpider(scrapy.Spider):
    name = "wawa"
    item_attributes = {"brand": "Wawa", "brand_wikidata": "Q5936320"}
    download_delay = 1.5
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}

    def start_requests(self) -> Iterable[Request]:
        for city in city_locations("US", 87000):
            yield JsonRequest(
                url="https://www.wawa.com/api/bff",
                data={
                    "query": "query FindNearLocations($latitude: Latitude!, $longitude: Longitude!) {\n  findNearLocations(latitude: $latitude, longitude: $longitude) {\n    results {\n      distance\n      name\n      scheduleType\n      storeOpen\n      storeClose\n      storeNumber\n      isStoreOpen\n      coordinates {\n        latitude\n        longitude\n      }\n      address {\n        address\n        city\n        state\n        zip\n      }\n      amenities {\n        food\n        fuel\n        restrooms\n        diesel\n        ethanolFreeGas\n        open24Hours\n        teslaChargingStation\n        propane\n        chademoChargingStation\n        ccsChargingStation\n      }\n      orderingAvailable\n      isCurbsideDeliveryAvailable\n      fuelTypes {\n        category\n      }\n    }\n  }\n}\n",
                    "variables": {"latitude": float(city["latitude"]), "longitude": float(city["longitude"])},
                },
                headers={
                    "content-type": "application/json",
                    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
                },
                method="POST",
            )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json()["data"]["findNearLocations"]["results"]:
            item = DictParser.parse(store)
            item["street_address"] = store["address"]["address"]
            apply_category(Categories.SHOP_CONVENIENCE, item)
            item["opening_hours"] = OpeningHours()
            if store["scheduleType"] == "24hours":
                item["opening_hours"] = "24/7"
            yield item
