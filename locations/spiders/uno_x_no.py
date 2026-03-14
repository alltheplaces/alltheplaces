from typing import Any

import chompjs
from scrapy import Spider
from scrapy.http import Response

from locations.categories import Access, Categories, Extras, Fuel, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import DAYS_EN, OpeningHours, sanitise_day
from locations.items import Feature


class UnoXNOSpider(Spider):
    name = "uno_x_no"
    allowed_domains = ["unox.no"]
    item_attributes = {"brand": "Uno-X", "brand_wikidata": "Q3362746"}
    start_urls = ["https://unox.no/umbraco/surface/MapData/Locations"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        locations = chompjs.parse_js_object(response.text)

        for location in locations:
            # Filter out other brand networks
            if location.get("IsOtherBrandNetwork"):
                continue

            item = DictParser.parse(location)
            item["street_address"] = item.pop("addr_full")
            item["branch"] = item.pop("name").removeprefix("Uno-X ").removeprefix("Truck ").removeprefix("EL ")
            if item["branch"].startswith("7-Eleven "):
                item["located_in"] = "7-Eleven"
                item["branch"] = item["branch"].removeprefix("7-Eleven ")

            item["ref"] = location.get("UnoxStationID")

            self.parse_opening_hours(location, item)
            self.parse_fuel_types(location, item)
            self.parse_services(location, item)
            self.parse_truck_products(location, item)
            self.parse_truck_services(location, item)
            self.apply_category(location, item)

            yield item

    def parse_opening_hours(self, location: dict, item: Feature):
        if opening_hours_data := location.get("OpeningHours"):
            oh = OpeningHours()
            for rule in opening_hours_data:
                day = rule.get("Day")
                opens = rule.get("Opens")
                closes = rule.get("Closes")
                if day and opens and closes:
                    day_normalized = sanitise_day(day, DAYS_EN)
                    if day_normalized:
                        # Format time strings (0600 -> 06:00)
                        if len(opens) == 4 and opens.isdigit():
                            opens = f"{opens[:2]}:{opens[2:]}"
                        if len(closes) == 4 and closes.isdigit():
                            closes = f"{closes[:2]}:{closes[2:]}"
                        oh.add_range(day_normalized, opens, closes)
            item["opening_hours"] = oh
        elif location.get("IsAlwaysOpen"):
            item["opening_hours"] = "24/7"

    def parse_fuel_types(self, location: dict, item: Feature):
        if gas_details := location.get("GasDetails"):
            gas_details_lower = gas_details.lower()
            if "95" in gas_details_lower or "blyfri" in gas_details_lower:
                apply_yes_no(Fuel.OCTANE_95, item, True)
            if "diesel" in gas_details_lower:
                apply_yes_no(Fuel.DIESEL, item, True)

    def parse_services(self, location: dict, item: Feature):
        if location.get("HasElectric"):
            apply_yes_no(Fuel.ELECTRIC, item, True)
        if location.get("HasWash"):
            apply_yes_no(Extras.CAR_WASH, item, True)
        if location.get("Has7Eleven"):
            apply_yes_no("food", item, True)
        if location.get("IsTruckFriendly") or location.get("IsPureTruckStop"):
            apply_yes_no(Access.HGV, item, True)

    def parse_truck_products(self, location: dict, item: Feature):
        if truck_products := location.get("TruckProductList"):
            for product in truck_products:
                product_lower = product.lower()
                if "diesel" in product_lower:
                    apply_yes_no(Fuel.HGV_DIESEL, item, True)
                if "avgfridiesel" in product_lower:
                    apply_yes_no(Fuel.UNTAXED_DIESEL, item, True)
                if "adblue" in product_lower:
                    apply_yes_no(Fuel.ADBLUE, item, True)
                if "hvo100" in product_lower:
                    apply_yes_no(Fuel.BIODIESEL, item, True)

    def parse_truck_services(self, location: dict, item: Feature):
        if truck_services := location.get("TruckServiceList"):
            for service in truck_services:
                service_lower = service.lower()
                if "matservering" in service_lower:
                    apply_yes_no("food", item, True)

    def apply_category(self, location: dict, item: Feature):
        has_gas = location.get("HasGas")
        has_electric = location.get("HasElectric")
        has_wash = location.get("HasWash")

        if has_gas:
            # Has fuel (gas) - always a fuel station
            apply_category(Categories.FUEL_STATION, item)
            apply_yes_no(Fuel.ELECTRIC, item, has_electric)
            apply_yes_no(Extras.CAR_WASH, item, has_wash)
        elif has_electric and not has_gas:
            # Only electric charging, no fuel
            apply_category(Categories.CHARGING_STATION, item)
            apply_yes_no(Extras.CAR_WASH, item, has_wash)
        elif has_wash and not has_gas and not has_electric:
            # Only car wash, no fuel or charging
            apply_category(Categories.CAR_WASH, item)
        else:
            # Default fallback
            apply_category(Categories.FUEL_STATION, item)
