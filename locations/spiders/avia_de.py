import scrapy

from locations.categories import (
    Access,
    Categories,
    Extras,
    Fuel,
    FuelCards,
    PaymentMethods,
    apply_category,
    apply_yes_no,
    map_payment,
)
from locations.dict_parser import DictParser

AVIA_SHARED_ATTRIBUTES = {
    "brand": "Avia",
    "brand_wikidata": "Q300147",
}

FUEL_TYPES_MAPPING = {
    "AdBlue (Gebinde)": Fuel.ADBLUE,
    "AdBlue Säule (LKW)": Fuel.ADBLUE,
    "AdBlue Säule (PKW)": Fuel.ADBLUE,
    "Blue Diesel": Fuel.DIESEL,
    "CNG/Erdgas": Fuel.CNG,
    "Diesel": Fuel.DIESEL,
    "LKW-Diesel": Fuel.HGV_DIESEL,
    "LPG/Autogas": Fuel.LPG,
    "Stromladesäule": Fuel.ELECTRIC,
    "Super E10": Fuel.E10,
    "Super E5": Fuel.E5,
    "Super Plus": Fuel.OCTANE_98,
}

SERVICES_MAPPING = {
    "Anhängervermietung": None,
    "Backshop": None,
    "Bistro": Extras.FAST_FOOD,
    "Dusche": Extras.SHOWERS,
    "Erdgas": None,
    "Geldautomat": Extras.ATM,
    "Getränkemarkt": None,
    "LKW-Hochleistungssäule": Access.HGV,
    "LOTTO": None,
    "Portalwaschanlage": Extras.CAR_WASH,
    "Prima Bistro": Extras.FAST_FOOD,
    "Reinigungsannahme": None,
    "SB-Sauger": Extras.VACUUM_CLEANER,
    "SB-Waschbox": None,
    "SB-Öltheke": None,
    "Segafredo Kaffee": None,
    "Shop": None,
    "Stromladesäule": Fuel.ELECTRIC,
    "Tankautomat": "automated",
    "TÜV / AU": None,
    "Unbemannte Automatenstation": None,
    "Waschstrasse": Extras.CAR_WASH,
    "Werkstatt": None,
}


class AviaDESpider(scrapy.Spider):
    name = "avia_de"
    allowed_domains = ["www.avia.de"]
    start_urls = ["https://www.avia.de/index.php?eID=tsfindergetdata&datatype=allstations"]
    BRANDS_MAPPING = {
        "AVIA Automatentankstelle": AVIA_SHARED_ATTRIBUTES,
        "AVIA Tankstelle": AVIA_SHARED_ATTRIBUTES,
        "AVIA XPress": AVIA_SHARED_ATTRIBUTES,
        "tankpoint Tankstelle": {"brand": "Tank Point"},
    }

    def parse(self, response):
        def dict_to_list(d):
            return d.values() if d else []

        for poi in response.json():
            poi.update(poi.pop("addressData"))
            poi.update(poi.pop("contactData"))
            poi.update(poi.pop("geoData"))
            item = DictParser.parse(poi)
            item.update(self.BRANDS_MAPPING.get(poi.get("facilityTitle"), {}))

            payments = dict_to_list(poi.get("optionalData", {}).get("paymentMethods"))
            fuel_cards = dict_to_list(poi.get("optionalData", {}).get("fuelCards", {}))
            gas_types = dict_to_list(poi.get("optionalData", {}).get("gasTypes", {}))
            services = dict_to_list(poi.get("optionalData", {}).get("services", {}))

            for payment in payments:
                if not map_payment(item, payment, PaymentMethods):
                    self.crawler.stats.inc_value(f"atp/avia_de/payment/fail/{payment}")

            for fuel_card in fuel_cards:
                if not map_payment(item, fuel_card, FuelCards):
                    self.crawler.stats.inc_value(f"atp/avia_de/fuelCard/fail/{fuel_card}")

            self.parse_attribute(item, gas_types, "gasTypes", FUEL_TYPES_MAPPING)
            self.parse_attribute(item, services, "services", SERVICES_MAPPING)

            apply_category(Categories.FUEL_STATION, item)

            # TODO: Opening hours
            yield item

    def parse_attribute(self, item, values: list, attribute_name, mapping: dict):
        for value in values:
            if tag := mapping.get(value):
                apply_yes_no(tag, item, True)
            else:
                self.crawler.stats.inc_value(f"atp/avia_de/{attribute_name}/fail/{value}")
