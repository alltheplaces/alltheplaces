import json
import re
from datetime import datetime

from scrapy import Spider

from locations.categories import Categories, Extras, Fuel, apply_category, apply_yes_no
from locations.hours import OpeningHours
from locations.items import Feature

FUEL_TYPES = {
    "Regular": Fuel.GASOLINE,
    "Unleaded 15": Fuel.E15,
    "Flex Fuel": Fuel.E85,
    "Ethanol Free": Fuel.ETHANOL_FREE,
    "Auto Diesel": Fuel.DIESEL,
    "Truck Diesel": Fuel.HGV_DIESEL,
    "DEF": Fuel.ADBLUE,
    "Off Road Diesel": Fuel.UNTAXED_DIESEL,
    "Kerosene": Fuel.KEROSENE,
}
DAYS = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")


class RuttersUSSpider(Spider):
    name = "rutters_us"
    item_attributes = {"brand": "Rutter's", "brand_wikidata": "Q7383544", "country": "US"}
    allowed_domains = ["www.rutters.com"]
    start_urls = ["https://www.rutters.com/stores/"]

    def parse(self, response):
        marker = re.search(r"\bvar\s+storesJSON\s*=\s*", response.text)
        if not marker:
            raise ValueError("Store data missing from Rutter's locator")
        stores, _ = json.JSONDecoder().raw_decode(response.text[marker.end() :])

        for store in stores.values():
            if store.get("post_status") != "publish":
                continue
            details = store["store_meta"]
            if details.get("is_closed"):
                continue

            item = Feature(
                ref=details["store_number"],
                branch=details["store_number"],
                lat=details["latitude"],
                lon=details["longitude"],
                street_address=details["address"],
                city=details["city"],
                state=details["state"],
                postcode=details["zip"],
                phone=details.get("phone_number"),
                website=response.url,
            )
            apply_category(Categories.FUEL_STATION, item)

            fuels = set(details.get("fuel_types") or [])
            for source_name, attribute in FUEL_TYPES.items():
                apply_yes_no(attribute, item, source_name in fuels)

            amenities = set(details.get("amenities") or [])
            for source_name, attribute in {
                "Surcharge Free ATM": Extras.ATM,
                "Free WiFi": Extras.WIFI,
                "Restrooms": Extras.TOILETS,
                "Car Wash": Extras.CAR_WASH,
                "Air Machine": Extras.COMPRESSED_AIR,
            }.items():
                apply_yes_no(attribute, item, source_name in amenities)

            if all(details.get(day) == "24 Hours" for day in DAYS):
                item["opening_hours"] = "24/7"
            else:
                hours = OpeningHours()
                for day in DAYS:
                    value = details.get(day, "")
                    if value == "24 Hours":
                        hours.add_range(day, "00:00", "23:59")
                    elif match := re.fullmatch(r"(\d{1,2}:\d{2} [AP]M) - (\d{1,2}:\d{2} [AP]M|Midnight)", value):
                        opening = datetime.strptime(match[1], "%I:%M %p").strftime("%H:%M")
                        closing = (
                            "24:00"
                            if match[2] == "Midnight"
                            else datetime.strptime(match[2], "%I:%M %p").strftime("%H:%M")
                        )
                        hours.add_range(day, opening, closing)
                if hours.as_opening_hours():
                    item["opening_hours"] = hours

            yield item
