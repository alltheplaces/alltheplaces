import scrapy
from scrapy.http import FormRequest

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
from locations.geo import country_coordinates
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
    "MOL Ceska Republika": ("MOL", "Q549181"),
    "MOLPLUGEE": ("MOL", "Q549181"),
    "PapOil": ("PapOil", None),
    "Slovnaft": ("Slovnaft", "Q1587563"),
    "TOTAL": ("Total", "Q154037"),
    "LOTOS": ("Lotos", "Q1256909"),
    "TOTAL ACCESS": ("Total Access", "Q154037"),
    "ex-OMV": ("MOL", "Q549181"),
}

FUEL_MAPPING = {
    "AdBlue": Fuel.ADBLUE,
    "CNG (Comprimed natural gas, in tank)": None,
    "EVO 100 Plus (GASOLINE PREMIUM)": Fuel.OCTANE_100,
    "EVO 95": Fuel.OCTANE_95,
    "EVO Diesel": Fuel.DIESEL,
    "EVO Diesel Plus (DIESEL PREMIUM)": Fuel.DIESEL,
    "LPG ": Fuel.LPG,
    "MOL Racing Fuel": "fuel:octane_102",
    "Maingrade 95": Fuel.OCTANE_95,
    "Premium Gasoline": Fuel.OCTANE_95,
    "Premium Diesel": Fuel.DIESEL,
    "Maingrade Diesel": Fuel.DIESEL,
    "RACING 102": "fuel:octane_102",
    "XXL Diesel": Fuel.DIESEL,
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
    # TODO: map high flow pump, this seems an important attribute for petrol stations!
    "High speed pump": None,
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
    allowed_domains = ["toltoallomaskereso.mol.hu"]

    def start_requests(self):
        country_coords = country_coordinates(return_lookup=True)
        for country in COUNTRIES.values():
            if coords := country_coords.get(country):
                yield FormRequest(
                    url="https://toltoallomaskereso.mol.hu/en/portlet/routing/along_latlng.json",
                    formdata={
                        "country": country,
                        "lat": coords[0],
                        "lng": coords[1],
                    },
                    meta={"country": country},
                )

    def parse(self, response):
        for poi in response.json():
            yield FormRequest(
                url="https://toltoallomaskereso.mol.hu/en/portlet/routing/station_info.json",
                formdata={"id": poi["id"]},
                callback=self.parse_poi,
                meta=response.meta,
            )

    def parse_poi(self, response):
        if poi := response.json():
            fs = poi.get("fs")
            item = DictParser.parse(fs)
            item["street_address"] = item.pop("addr_full", None)
            item["country"] = response.meta.get("country")
            item["phone"] = "; ".join(filter(None, [fs.get("fs_phone_num"), fs.get("fs_mobile_num")]))
            self.parse_attribute(item, poi, "products", FUEL_MAPPING)
            self.parse_attribute(item, poi, "cards", CARDS_MAPPING)
            self.parse_attribute(item, poi, "services", SERVICES_MAPPING)
            self.parse_brand(item, poi)
            self.parse_hours(item, poi)
            apply_category(Categories.FUEL_STATION, item)
            yield item

    def parse_attribute(self, item, data: dict, attribute_name: str, mapping: dict):
        for attribute in data.get(attribute_name, []):
            name = attribute.get("name")
            if tag := mapping.get(name):
                apply_yes_no(tag, item, True)
            else:
                self.crawler.stats.inc_value(f"atp/mol/{attribute_name}/failed/{name}")

    def parse_brand(self, item, poi):
        if brand_details := BRANDS_MAPPING.get(poi.get("brand", {}).get("name")):
            brand, brand_wikidata = brand_details
            item["brand"] = brand
            item["brand_wikidata"] = brand_wikidata
        else:
            self.crawler.stats.inc_value(f"atp/mol/unknown_brands/{poi.get('brand', {}).get('name')}")

    def parse_hours(self, item, poi):
        fs = poi.get("fs", {})
        oh = OpeningHours()
        try:
            for k, v in fs.items():
                # There are winter and summer hours available.
                # to keep it simple parse only winter hours.
                if k.startswith("opn_hrs_wtr_"):
                    days = k.split("_")[-1]
                    time_open, time_close = v.split("-")
                    if days == "wd":
                        oh.add_days_range(NAMED_DAY_RANGES_EN.get("Weekdays"), time_open, time_close)
                    elif days == "sat":
                        oh.add_range("Sa", time_open, time_close)
                    elif days == "sun":
                        oh.add_range("Sa", time_open, time_close)
            item["opening_hours"] = oh.as_opening_hours()
        except Exception as e:
            self.logger.warning(f"Failed to parse hours: {fs}, {e}")
