from typing import Iterable

import scrapy
from scrapy import Request
from scrapy.http import Response

from locations.categories import Categories, Fuel, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature

FUEL_TYPES_MAPPING = {
    "Supreme": Fuel.OCTANE_91,
    "Ultra93": Fuel.OCTANE_93,
    "Ultra94": Fuel.OCTANE_94,
    "Gasoline": Fuel.OCTANE_87,
    "Diesel": Fuel.DIESEL,
    "DyedDiesel": Fuel.UNTAXED_DIESEL,
    "PropaneAutomotive": Fuel.PROPANE,
    "NaturalGasForVehicles": Fuel.CNG,
    "BulkDef": Fuel.ADBLUE,
    "PropaneBottleFills": Fuel.PROPANE,
    "ElectricChargingStation": Fuel.ELECTRIC,
    "SuperClean94": Fuel.OCTANE_94,
    # TODO: confirm these fuel types
    "DyedGasoline": None,
    "WinterGas": None,
    "PropaneBottleExchange": None,
}


class PetroCanadaCASpider(scrapy.Spider):
    name = "petro_canada_ca"
    requires_proxy = True
    item_attributes = {"brand": "Petro-Canada", "brand_wikidata": "Q1208279"}
    start_urls = [
        "https://www.petro-canada.ca/en/api/petrocanada/locations?limit=10000000&range=10000000",
    ]

    def parse(self, response: Response) -> Iterable[Request]:
        data = response.json()
        for store in data:
            yield scrapy.Request(
                "https://www.petro-canada.ca/en/api/petrocanada/locations/{}".format(store["Id"]),
                callback=self.parse_store,
            )

    def parse_store(self, response: Response) -> Iterable[Feature]:
        yield from self.parse_store_data(response.json())

    def parse_store_data(self, store: dict) -> Iterable[Feature]:
        item = DictParser.parse(store)
        item["street_address"] = store["AddressLine"]
        item["street"] = store["CrossStreet"]
        item["city"] = store["PrimaryCity"]
        item["state"] = store["Subdivision"]

        oh = OpeningHours()
        if opening_hours := store.get("Hours"):
            for day in DAYS_FULL:
                start = opening_hours[day[:3] + "OpenHr"].replace("9500", "0500")
                end = opening_hours[day[:3] + "CloseHr"].replace("2400", "2359")
                if start and end:
                    oh.add_range(day, start, end, time_format="%H%M")
        item["opening_hours"] = oh

        self.apply_website(item)
        self.parse_fuel_types(item, store)
        apply_category(Categories.FUEL_STATION, item)
        yield item

    def parse_fuel_types(self, item: Feature, store: dict) -> None:
        if fuel_types := store.get("FuelTypes"):
            for fuel_key, fuel_available in fuel_types.items():
                if fuel_available:
                    if fuel_enum := FUEL_TYPES_MAPPING.get(fuel_key):
                        apply_yes_no(fuel_enum, item, True)
                    else:
                        self.crawler.stats.inc_value(f"atp/{self.name}/fuel/unknown/{fuel_key}")

    def apply_website(self, item: Feature) -> None:
        item["website"] = "https://www.petro-canada.ca/en/personal/gas-station-locations/{}-{}".format(
            "".join(char for char in item["street_address"] if char.isalnum()),
            "".join(char for char in item["city"] if char.isalnum()),
        )
