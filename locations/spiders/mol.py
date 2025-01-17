from typing import Any, Iterable

import scrapy
from scrapy import Request
from scrapy.http import JsonRequest, Response

from locations.categories import (
    Access,
    Categories,
    Extras,
    Fuel,
    FuelCards,
    PaymentMethods,
    apply_category,
    apply_yes_no,
)
from locations.dict_parser import DictParser
from locations.hours import NAMED_DAY_RANGES_EN, OpeningHours

COUNTRIES = {
    "2": "BA",
    "3": "CZ",
    "5": "AT",
    "6": "HR",
    "7": "SI",
    "8": "SK",
    "9": "HU",
    "10": "RO",
    "11": "RS",
    "22": "ME",
    "121": "PL",
    "141": "BE",
    "142": "DE",
    "143": "FR",
    "144": "NL",
    "145": "LU",
}

BRANDS_MAPPING = {
    "INA": ("INA", "Q1662137"),
    "MOL": ("MOL", "Q549181"),
    "MOL (AGIP)": ("MOL", "Q549181"),
    "MOL CESKA REPUBLIKA": ("MOL", "Q549181"),
    "MOLPLUGEE": ("MOL", "Q549181"),
    "PAPOIL": ("PapOil", None),
    "SLOVNAFT": ("Slovnaft", "Q1587563"),
    "TOTAL": ("Total", "Q154037"),
    "LOTOS": ("Lotos", "Q1256909"),
    "TOTAL ACCESS": ("TotalEnergies", "Q154037"),
    "EX-OMV": ("MOL", "Q549181"),
    "TIFON": ("Tifon", None),
    "ENERGOPETROL": ("Energopetrol", "Q120433"),
}

FUEL_MAPPING = {
    "ADBLUE": Fuel.ADBLUE,
    "BLUE DIESEL": Fuel.DIESEL,
    "CNG": Fuel.CNG,
    "DIESEL": Fuel.DIESEL,
    "DYNAMIC DIESEL": Fuel.DIESEL,
    "EVO 100 PLUS (GASOLINE PREMIUM)": Fuel.OCTANE_100,
    "EVO 100 PLUS": Fuel.OCTANE_100,
    "EVO 100": Fuel.OCTANE_100,
    "EVO 95": Fuel.OCTANE_95,
    "EVO 95 PLUS": Fuel.OCTANE_95,
    "EVO 98 PLUS": Fuel.OCTANE_98,
    "EUROSUPER 100 CLASS PLUS": Fuel.OCTANE_100,
    "EUROSUPER 95": Fuel.OCTANE_95,
    "EUROSUPER 95 CLASS PLUS": Fuel.OCTANE_95,
    "EVO DIESEL": Fuel.DIESEL,
    "EURODIESEL": Fuel.DIESEL,
    "EURODIESEL CLASS PLUS": Fuel.DIESEL,
    "EVO DIESEL PLUS WINTER DIESEL": Fuel.COLD_WEATHER_DIESEL,
    "EVO DIESEL PLUS (DIESEL PREMIUM)": Fuel.DIESEL,
    "EVO DIESEL PLUS": Fuel.DIESEL,
    "LPG": Fuel.LPG,
    "MOL RACING FUEL": "fuel:octane_102",
    "MAINGRADE 95": Fuel.OCTANE_95,
    "PREMIUM GASOLINE": Fuel.OCTANE_95,
    "PREMIUM DIESEL": Fuel.DIESEL,
    "MAINGRADE DIESEL": Fuel.DIESEL,
    "MAINGRADE 95 PLUS": Fuel.OCTANE_95,
    "RACING 102": "fuel:octane_102",
    "XXL DIESEL": Fuel.DIESEL,
}

SERVICES_MAPPING = {
    "Air/Compresor": Extras.COMPRESSED_AIR,
    "Automatic car wash": Extras.CAR_WASH,
    "Big enough to fit a truck": Access.HGV,
    "Disabled toilet": Extras.TOILETS_WHEELCHAIR,
    "Family Toilet": Extras.TOILETS,
    "Hamburger": "fast_food",
    "Hoover": Extras.VACUUM_CLEANER,
    "Hot dog": "fast_food",
    "Internet (wifi)": Extras.WIFI,
    "Lubricant": Fuel.ENGINE_OIL,
    "Shower room": Extras.SHOWERS,
    "Truck friendly": Access.HGV,
    "Truck park": Access.HGV,
    "Jet wash": Extras.CAR_WASH,
    "High speed pump": Fuel.HGV_DIESEL,
    # TODO: map below services if possible
    "Cylinder PB Gas": None,
    "Defibrillator - AED": None,
    "Pharmacy": None,
}

CARDS_MAPPING = {
    "AMEX": PaymentMethods.AMERICAN_EXPRESS,
    "AS24": FuelCards.AS24,
    "CCS Card": None,
    "Cirrus/ Maestro": PaymentMethods.MAESTRO,
    "Diners": PaymentMethods.DINERS_CLUB,
    "Discover": PaymentMethods.DISCOVER_CARD,
    "DKV Card": FuelCards.DKV,
    "EURO OIL": None,
    "EURO WAG": FuelCards.EUROWAG,
    "E100 Card": FuelCards.E100,
    "Energopetrol Gold Card BiH": None,
    "Euroshell card": FuelCards.SHELL,
    "Eurocard/ Mastercard": PaymentMethods.MASTER_CARD,
    "INA Card": FuelCards.INA,
    "Maestro": PaymentMethods.MAESTRO,
    "MasterCard Electronic": PaymentMethods.MASTER_CARD,
    "MOL Blue Card HU": FuelCards.MOLGROUP_CARDS,
    "MOL Blue Card RO": FuelCards.MOLGROUP_CARDS,
    "MOL Employee Card HU": None,
    "MOL Green Card RO": FuelCards.MOLGROUP_CARDS,
    "MOL Loyalty Card HU": None,
    "MOL Silver Card CZ": FuelCards.MOLGROUP_CARDS,
    "MOL Gold Card HU": FuelCards.MOLGROUP_CARDS,
    "MOL Gold Card RO": FuelCards.MOLGROUP_CARDS,
    "MOL Gold Card SRB": FuelCards.MOLGROUP_CARDS,
    "MOL Gold Card SLO": FuelCards.MOLGROUP_CARDS,
    "MOL Silver Card HU": FuelCards.MOLGROUP_CARDS,
    "MOL Red Card HU": FuelCards.MOLGROUP_CARDS,
    "MOL Green Card HU": FuelCards.MOLGROUP_CARDS,
    "MOL Gold Card AT": FuelCards.MOLGROUP_CARDS,
    "MOL RED Card RO": FuelCards.MOLGROUP_CARDS,
    "MOL Red Card SLO": FuelCards.MOLGROUP_CARDS,
    "MOL Gold Card CZ": FuelCards.MOLGROUP_CARDS,
    "MOL Silver Card RO": FuelCards.MOLGROUP_CARDS,
    "Morgan Fuels": FuelCards.MORGAN_FUELS,
    "Slovnaft Gold Card SK": FuelCards.SLOVNAFT,
    "Slovnaft Red Card SK": FuelCards.SLOVNAFT,
    "Tifon Gold Card HR": FuelCards.TIFON,
    "VPay": PaymentMethods.V_PAY,
    "Vemex CNG": None,
    "VISA": PaymentMethods.VISA,
    "VISA Electron": PaymentMethods.VISA_ELECTRON,
    "UTA Card": FuelCards.UTA,
}


# MOL data is also available at https://www.molgroupcards.com/station-finder
# along with other brands, but not all POIs on this page have fuel types and services.
class MolSpider(scrapy.Spider):
    name = "mol"
    custom_settings = {"ROBOTSTXT_OBEY": False}
    download_timeout = 90

    def start_requests(self) -> Iterable[Request]:
        for country in COUNTRIES.values():
            yield JsonRequest(
                url="https://tankstellenfinder.molaustria.at/api.php",
                data={
                    "api": "stations",
                    "mode": "country",
                    "input": country,
                },
                meta={"country": country},
            )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for poi in response.json():
            poi.update(poi.pop("gpsPosition"))
            if not poi.get("latitude") and not poi.get("address"):  # not enough location data
                continue
            poi.pop("county", None)  # sometimes contains country info
            item = DictParser.parse(poi)
            item["ref"] = poi.get("code")
            item["street_address"] = item.pop("addr_full", None)
            item["country"] = response.meta.get("country")
            item["phone"] = "; ".join(filter(None, [poi.get("phoneNum"), poi.get("mobileNum")]))
            self.parse_attribute(item, poi, "fuelsAndAdditives", FUEL_MAPPING)
            self.parse_attribute(item, poi, "cards", CARDS_MAPPING)
            self.parse_attribute(item, poi, "services", SERVICES_MAPPING)
            self.parse_brand(item, poi)
            self.parse_hours(item, poi)
            apply_category(Categories.FUEL_STATION, item)
            yield item

    def parse_attribute(self, item, data: dict, attribute_name: str, mapping: dict) -> Any:
        for attribute in data.get(attribute_name, {}).get("values", []):
            name = attribute.get("name")
            if attribute_name == "fuelsAndAdditives":
                name = name.upper() if name else ""
            if tag := mapping.get(name):
                apply_yes_no(tag, item, True)
            else:
                self.crawler.stats.inc_value(f"atp/mol/{attribute_name}/failed/{name}")

    def parse_brand(self, item, poi) -> Any:
        brand_key = poi["brand"].upper() if poi.get("brand") else ""
        if brand_details := BRANDS_MAPPING.get(brand_key):
            brand, brand_wikidata = brand_details
            item["brand"] = brand
            item["brand_wikidata"] = brand_wikidata
        else:
            self.crawler.stats.inc_value(f"atp/mol/unknown_brands/{poi.get('brand')}")

    def parse_hours(self, item, poi) -> Any:
        hours = poi.get("openedHours", {})
        oh = OpeningHours()
        try:
            for k, v in hours.items():
                # There are winter and summer hours available.
                # to keep it simple parse only winter hours.
                if k.startswith("openedWinter"):
                    day = k.split("openedWinter")[-1]
                    time_open, time_close = v.split("-")
                    if day == "WeekDay":
                        oh.add_days_range(NAMED_DAY_RANGES_EN.get("Weekdays"), time_open, time_close)
                    else:
                        oh.add_range(day, time_open, time_close)
            item["opening_hours"] = oh
        except Exception as e:
            self.logger.warning(f"Failed to parse hours: {hours}, {e}")
