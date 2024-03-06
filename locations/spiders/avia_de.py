import scrapy

from locations.categories import Categories, Fuel, FuelCards, PaymentMethods, apply_category, apply_yes_no, map_payment
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
        for poi in response.json():
            poi.update(poi.pop("addressData"))
            poi.update(poi.pop("contactData"))
            poi.update(poi.pop("geoData"))
            item = DictParser.parse(poi)
            item.update(self.BRANDS_MAPPING.get(poi.get("facilityTitle"), {}))

            if payment := poi.get("optionalData", {}).get("paymentMethods", {}):
                for paymentMethod in payment.values():
                    if not map_payment(item, paymentMethod, PaymentMethods):
                        self.crawler.stats.inc_value(f"atp/avia_de/payment/fail/{paymentMethod}")

            if fuel_cards := poi.get("optionalData", {}).get("fuelCards", {}):
                for fuelCard in fuel_cards.values():
                    if not map_payment(item, fuelCard, FuelCards):
                        self.crawler.stats.inc_value(f"atp/avia_de/fuelCard/fail/{fuelCard}")

            for fuel in poi.get("optionalData", {}).get("fuelTypes", []):
                if tag := FUEL_TYPES_MAPPING.get(fuel):
                    apply_yes_no(tag, item, True)
                else:
                    self.crawler.stats.inc_value(f"atp/avia_de/fuel/fail/{fuel}")

            apply_category(Categories.FUEL_STATION, item)

            # TODO: Opening hours
            yield item
