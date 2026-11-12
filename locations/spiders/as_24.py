from typing import Iterable

from locations.categories import Access, Categories, Extras, Fuel, apply_category, apply_yes_no
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider

# Product, service and station type identifiers are defined in the station
# finder's JavaScript bundle, https://network.as24.com/stationfinder/main.js
FUEL_MAPPING = {
    "01": Fuel.UNTAXED_DIESEL,
    "03": Fuel.DIESEL,
    "04": Fuel.HEATING_OIL,
    "06": Fuel.BIODIESEL,
    "95": "fuel:hvo100",
    "9A": "fuel:hvo20",
    "10": Fuel.ADBLUE,
    "GC": Fuel.CNG,
    "GL": Fuel.LNG,
    "BIOGNC": (Fuel.CNG, Fuel.BIOGAS),
    "W1": Fuel.ELECTRIC,
    "W2": Fuel.ELECTRIC,
    "W3": Fuel.ELECTRIC,
}

TRUCK_WASH = "TW1"
TANK_WASH = "TC1"
PARKING = "PK1"

# Station types 1, 2, 3 and 7 are fuel stations, type 4 are the fuel stations of
# the acceptance network, and type 10 are the wash and parking sites of AS 24's
# partner network (Travis), which carry no AS 24 brand.
WASH_AND_PARKING_STATION_TYPE = 10

UNAVAILABLE_STATUS = 3

# Only the French fuel stations are branded AS 24, elsewhere the network is a mix
# of AS 24 and partner brands which the feed does not distinguish.
FRANCE = "FRA"

# Station finder languages, other countries get the English page
WEBSITE_LANGUAGES = {
    "AUT": "de",
    "BGR": "bg",
    "CZE": "cs",
    "DEU": "de",
    "ESP": "es",
    "FRA": "fr",
    "HRV": "hr",
    "HUN": "hu",
    "ITA": "it",
    "LTU": "lt",
    "LUX": "fr",
    "NLD": "nl",
    "POL": "pl",
    "PRT": "pt",
    "ROU": "ro",
    "SVN": "sl",
    "UKR": "uk",
}

PARKING_BOOKING_MAPPING = {
    0: None,
    1: Extras.RESERVATION,
    2: Extras.RESERVATION_REQUIRED,
}


class As24Spider(JSONBlobSpider):
    name = "as_24"
    AS_24 = {"brand": "AS 24", "brand_wikidata": "Q2819394"}
    start_urls = ["https://network.as24.com/stationfinderservices/services/stationsWithDetails?langueId=en"]

    def pre_process_data(self, feature: dict) -> None:
        feature["postcode"] = feature.pop("cityCode")

    def post_process_item(self, item: Feature, _, feature: dict) -> Iterable[Feature]:
        if feature["status"] == UNAVAILABLE_STATUS:
            return
        item["ref"] = feature["stationId"]
        item["street_address"] = item.pop("addr_full")
        language = WEBSITE_LANGUAGES.get(feature["countryCode"], "en")
        item["website"] = f"https://network.as24.com/stationfinder/{language}/stations/{item['ref']}"
        apply_yes_no(Access.HGV, item, True)

        if feature["stationType"] == WASH_AND_PARKING_STATION_TYPE:
            self.parse_wash_and_parking(item, feature)
        else:
            apply_category(Categories.FUEL_STATION, item)
            self.parse_fuel(item, feature)
            if feature["countryCode"] == FRANCE:
                item.update(self.AS_24)
                item["branch"] = item.pop("name")

        yield item

    def parse_wash_and_parking(self, item: Feature, poi: dict) -> None:
        services = poi["services"] or {}
        if TRUCK_WASH in services or TANK_WASH in services:
            apply_category(Categories.CAR_WASH, item)
            apply_yes_no(Extras.TRUCK_WASH, item, TRUCK_WASH in services)
            # https://taginfo.openstreetmap.org/keys/tank_cleaning_truck
            apply_yes_no("tank_cleaning_truck", item, TANK_WASH in services)
            apply_yes_no("hgv:parking", item, PARKING in services)
            self.parse_hours(item, poi["washingOpeningHours"] or poi["tankCleaningOpeningHours"])
        elif PARKING in services:
            apply_category(Categories.PARKING, item)
            self.parse_hours(item, poi["parkingOpeningHours"])
            if booking := PARKING_BOOKING_MAPPING.get(poi["parkingBooking"]):
                apply_yes_no(booking, item, True)
        else:
            self.crawler.stats.inc_value(f"atp/{self.name}/unknown_wash_and_parking_site/{sorted(services)}")

    @staticmethod
    def parse_hours(item: Feature, hours: dict | None) -> None:
        oh = OpeningHours()
        for day, day_hours in (hours or {}).items():
            for slot in day_hours["timeSlots"]:
                if slot["isOpenAllDay"]:
                    oh.add_range(day, "00:00", "24:00")
                else:
                    oh.add_range(day, slot["start"], slot["end"])
        if oh.day_hours:
            item["opening_hours"] = oh

    def parse_fuel(self, item: Feature, poi: dict) -> None:
        for fuel in poi["products"] or {}:
            if tags := FUEL_MAPPING.get(fuel):
                for tag in tags if isinstance(tags, tuple) else (tags,):
                    apply_yes_no(tag, item, True)
            else:
                self.crawler.stats.inc_value(f"atp/{self.name}/fuel/unknown/{fuel}")
