import scrapy
from scrapy.http import FormRequest
from locations.dict_parser import DictParser

from locations.geo import country_coordinates
from locations.categories import Fuel, Categories, FuelCards, apply_category, apply_yes_no, Extras, PaymentMethods


FUEL_MAPPING = {
    'Maingrade 95': Fuel.OCTANE_95,
    'Premium Gasoline': Fuel.OCTANE_95,
    'Premium Diesel': Fuel.DIESEL,
    'Maingrade Diesel': Fuel.DIESEL,
    'EVO 100 Plus (GASOLINE PREMIUM)': Fuel.OCTANE_100,
    'EVO 95': Fuel.OCTANE_95,
    'EVO Diesel Plus (DIESEL PREMIUM)': Fuel.DIESEL,
    'AdBlue': Fuel.ADBLUE,
}

SERVICES_MAPPING = {
  "Shop": None,
  "Pre-packed sandwich": None,
  "Hoover": None,
  "Jet wash": Extras.CAR_WASH,
  "Air/Compresor": Extras.COMPRESSED_AIR,
  "Lubricant": Fuel.ENGINE_OIL,
  "Internet (wifi)": Extras.WIFI,
  "Hungarian Motorway Vignette": None,
  "Cylinder PB Gas": None,
  "Used cooking oil": None,
  "EURO payment acceptance": None,
  # TODO: map high speed pump
  "High speed pump": None,
  "Truck park": 'capacity:hgv=yes',
  "Toll terminal": None,
  "Fresh Coffee TO GO": None,
  "Dog chip reader place (free)": None,
  "Dog friendly": None,
  "ENP - Electronically paying toll ": None,
  "MOL Hygi": None,
  "Base station for Food truck/Tuk-tuk": None,
  "Fresh Coffee TOGO": None,
  "Barista Coffee": None,
  "MOL Shop": None
}

CARDS_MAPPING = {
  "DKV Card": FuelCards.DKV,
  "UTA Card": FuelCards.UTA,
  "VISA": PaymentMethods.VISA,
  "VISA Electron": PaymentMethods.VISA_ELECTRON,
  "Eurocard/ Mastercard": PaymentMethods.MASTER_CARD,
  "Maestro": PaymentMethods.MAESTRO,
  "AMEX": PaymentMethods.AMERICAN_EXPRESS,
  "MasterCard Electronic": PaymentMethods.MASTER_CARD,
  "MOL Gold Card HU": FuelCards.MOLGROUP_CARDS,
  "Slovnaft Gold Card SK": FuelCards.SLOVNAFT,
  "MOL Gold Card RO": FuelCards.MOLGROUP_CARDS,
  "MOL Gold Card SRB": FuelCards.MOLGROUP_CARDS,
  "MOL Gold Card SLO": FuelCards.MOLGROUP_CARDS,
  "MOL Silver Card HU": FuelCards.MOLGROUP_CARDS,
  "MOL Red Card HU": FuelCards.MOLGROUP_CARDS,
  "MOL Green Card HU": FuelCards.MOLGROUP_CARDS,
  "INA Card": FuelCards.INA,
  "Multipont Card HU": None,
  "MOL Gold Card AT": FuelCards.MOLGROUP_CARDS,
  "Tifon Gold Card HR": None,
  "MOL RED Card RO": FuelCards.MOLGROUP_CARDS,
  "Energopetrol Gold Card BiH": None,
  "MOL Gold Card CZ": FuelCards.MOLGROUP_CARDS,
  "E100 Card": FuelCards.E100,
  "Morgan Fuels": None,
  "MOL Red Card SLO": FuelCards.MOLGROUP_CARDS,
  "AS24": FuelCards.AS24,
  "Gold Card Europe": None,
  "Gold Card Hungary": None,
  "Gift Card Hungary": None,
  "Partner Card Hungary": None,
  "Gold Card Hungary Prepaid": None
}

class MolSpider(scrapy.Spider):
    name = "mol"
    allowed_domains = ["toltoallomaskereso.mol.hu"]

    def start_requests(self):
        country_coords = country_coordinates(return_lookup=True)
        self.logger.info(country_coords)
        for country in ["HU", "RO", "SL", "CZ", "SR"]:
            if coords := country_coords.get(country):
                yield FormRequest(
                    url="https://toltoallomaskereso.mol.hu/en/portlet/routing/along_latlng.json",
                    formdata={
                        "country": country,
                        "lat": coords[0],
                        "lng": coords[1],
                    },
                )

    def parse(self, response):
        for poi in response.json():
            yield FormRequest(
                url="https://toltoallomaskereso.mol.hu/en/portlet/routing/station_info.json",
                formdata={"id": poi["id"]},
                callback=self.parse_poi,
            )

    def parse_poi(self, response):
        if poi := response.json():
            fs = poi.get("fs")
            item = DictParser.parse(fs)
            apply_category(Categories.FUEL_STATION, item)
            item['phone'] = '; '.join(filter(None, [fs.get('fs_phone_num'), fs.get('fs_mobile_num')]))
            yield item

    def parse_attribute(self, item, data: dict, attribute_name: str, mapping: dict):
        for attribute in data.get(attribute_name, []):
            name = attribute.get("name")
            if tag := mapping.get(name):
                apply_yes_no(tag, item, True)
            else:
                self.crawler.stats.inc_value(f"atp/mol/{attribute_name}/failed/{name}")
