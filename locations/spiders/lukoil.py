import scrapy
from scrapy.http import JsonRequest

from locations.categories import Categories, Extras, Fuel, FuelCards, PaymentMethods, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.items import Feature

FUEL_TYPES_MAPPING = {
    Fuel.OCTANE_80: ["80"],
    Fuel.OCTANE_87: ["rbob-87"],
    Fuel.OCTANE_89: ["rbob-89"],
    Fuel.OCTANE_92: ["92-ecto", "92-euro"],
    Fuel.OCTANE_93: ["93"],
    Fuel.OCTANE_95: ["95-euro", "95-ecto", "95-ecto-plus", "euro-luk", "petrol-95-ethanol"],
    Fuel.OCTANE_98: ["98-ecto", "98-euro"],
    Fuel.OCTANE_100: ["100-ecto", "100-euro"],
    Fuel.DIESEL: ["dt-ecto", "dt-euro", "dt", "diesel-ecto-with-fame", "marked-diesel"],
    Fuel.LPG: ["lpg-auto", "gaz", "gpl-auto"],
    Fuel.KEROSENE: ["kerosene"],
    Fuel.HEATING_OIL: ["heating-oil"],
}

LUKOIL_BRAND = {"brand": "Лукойл", "brand_wikidata": "Q329347"}

COMPANY_BRANDS = {
    # Companies under Lukoil brand
    "Lukoil": LUKOIL_BRAND,
    "ЛУКОЙЛ": LUKOIL_BRAND,
    "LICARD": LUKOIL_BRAND,
    # Companies owned by Lukoil, but having other brand
    "Teboil": {"brand": "Teboil", "brand_wikidata": "Q7692079"},
}

PAYMENT_TYPES = {
    "ARIS Poland fuel card": FuelCards.ARIS,
    "ARIS fuel card": FuelCards.ARIS,
    "American Express": PaymentMethods.AMERICAN_EXPRESS,
    "Bank cards": PaymentMethods.CARDS,
    "Cash": PaymentMethods.CASH,
    "Contactless Payments": PaymentMethods.CONTACTLESS,
    "DKV fuel card": FuelCards.DKV,
    "E-100 fuel card": FuelCards.E100,
    "EuroShell fuel card": FuelCards.SHELL,
    "Fast payment system": PaymentMethods.SBP,
    "LUKOIL fuel card": FuelCards.LUKOIL,
    "LUKOIL FleetCard": FuelCards.LUKOIL,
    "LUKOIL loyalty card payment": FuelCards.LUKOIL_LOYALTY_PROGRAM,
    "Maestro": PaymentMethods.MAESTRO,
    "Non-cash payment methods": PaymentMethods.CARDS,
    "Petrol +Region fuel card": FuelCards.PETROL_PLUS_REGION,
    "Rosneft fuel card": FuelCards.ROSNEFT,
    "UTA fuel card": FuelCards.UTA,
    "Vpay": PaymentMethods.V_PAY,
    "Карта AMEX": PaymentMethods.AMERICAN_EXPRESS,
    # TODO: find payment methods for the following
    '"Халва" cards': None,
    "Bancontact/mister cash": None,
    "Gift Cards": None,
    "Inforcom fuel card": None,
    "Travelcard": None,
    "Postpay": None,
}

SERVICES = {
    "ATM ": Extras.ATM,
    "Car Wash": Extras.CAR_WASH,
    "Diesel Exhaust Fluid": Fuel.ADBLUE,
    "Diesel exhaust fluid (AdBlue)": Fuel.ADBLUE,
    "Hot Dog Sales": "fast_food=hotdog",
    "Restroom": Extras.TOILETS,
    "Wi-Fi": Extras.WIFI,
    "air tower": Extras.COMPRESSED_AIR,
    "handicap accessible restroom": Extras.TOILETS_WHEELCHAIR,
    # Values below are not mapped as they should exist as separate POIs,
    # or already mapped in other attributes, or not possible to map at all.
    "ASE": None,
    "Auto Repairs": None,
    "Autodor payment system acceptance": None,
    "C-Store": None,
    "Cash advance": None,
    "Cashback": None,
    "Coffee": None,
    "EPOS terminal (electronic point of sales)": None,
    "Electric charge": None,
    "Full Service Gas": None,
    "Hotel / Motel": None,
    "Insurance": None,
    "Kids corner": None,
    "Laundry": None,
    "Lukoil Loyalty Card acceptance": None,
    "Lukoil Loyalty Card distribution": None,
    "Lukoil Loyalty Card rewards acceptance": None,
    "Lukoil Rapida Credit Card (Sign in)": None,
    "Lukoil Rapida Credit Card (pay balance)": None,
    "Mobile phone recharge": None,
    "None": None,
    "Oil Change": None,
    "Paid parking": None,
    "Parking": None,
    "Playground": None,
    "Rapida payment system acceptance": None,
    'Refill "Platon"': None,
    "State Inspection": None,
    "Truck Stop": None,
    "Vacuum": None,
    "border crossing payments acceptance": None,
    "marketing promotions": None,
    "road tax vignette (sales)": None,
    "tire shop": None,
    "toll payments acceptance": None,
}

PROPERTIES = {
    "Cafe": None,
    # TODO: map high flow diesel pump, this seems an important attribute for petrol station!
    "High Flow Diesel": None,
}


class LukoilSpider(scrapy.Spider):
    name = "lukoil"
    download_delay = 0.10
    custom_settings = {"ROBOTSTXT_OBEY": False}
    handle_httpstatus_list = [403]

    def start_requests(self):
        yield JsonRequest(
            "https://lukoil.bg/api/cartography/GetCountryDependentSearchObjectData?form=gasStation",
            callback=self.get_results,
        )

    def get_results(self, response):
        for station in response.json()["GasStations"]:
            yield JsonRequest(f"https://lukoil.bg/api/cartography/GetObjects?ids=gasStation{station['GasStationId']}")

    def parse(self, response):
        if data := response.json()[0]:
            poi = data.get("GasStation")
            item = DictParser.parse(poi)
            item["ref"] = poi.get("GasStationId")
            item["image"] = poi.get("StationPhotoUrl")
            self.parse_brand(item, poi)
            self.parse_attribute(item, poi, "PaymentTypes", PAYMENT_TYPES)
            self.parse_attribute(item, poi, "Services", SERVICES)
            self.parse_attribute(item, poi, "Properties", PROPERTIES)
            self.parse_hours(item, poi)
            self.parse_fuel_types(item, data)
            apply_category(Categories.FUEL_STATION, item)
            yield item

    def parse_brand(self, item: Feature, poi: dict):
        if company_name := poi.get("Company", {}).get("Name", ""):
            for brand, brand_tags in COMPANY_BRANDS.items():
                if brand.lower() in company_name.lower():
                    item["brand"] = brand_tags["brand"]
                    item["brand_wikidata"] = brand_tags["brand_wikidata"]
                    break
            else:
                self.logger.warning(f"Unknown brand: {company_name}")
                self.crawler.stats.inc_value(f"atp/lukoil/brand/failed/{company_name}")

    def parse_attribute(self, item: Feature, poi: dict, attribute_name: str, mapping: dict):
        for attribute_entity in poi.get(attribute_name, []):
            if tag := mapping.get(attribute_entity.get("Name")):
                apply_yes_no(tag, item, True)
            else:
                pass
                # self.crawler.stats.inc_value(f"atp/lukoil/{attribute_name}/failed/{attribute_entity.get('Name')}")

    def parse_hours(self, item: Feature, poi: dict):
        if poi.get("TwentyFourHour"):
            item["opening_hours"] = "24/7"
            return
        try:
            oh = OpeningHours()
            if poi.get("StationBusinessHours") is not None:
                for index, time in enumerate(poi.get("StationBusinessHours", {}).get("Days")):
                    if time is not None:
                        if time["EndTime"] == "1.00:00:00":
                            time["EndTime"] = "23:59:00"
                        oh.add_range(DAYS[index], time["StartTime"], time["EndTime"], time_format="%H:%M:%S")
                item["opening_hours"] = oh
        except:
            self.crawler.stats.inc_value("atp/lukoil/hours/failed")

    def parse_fuel_types(self, item: Feature, data: dict):
        if fuels := data.get("Fuels"):
            for fuel_type in fuels:
                # Use fuel icon to determine fuel type as fuel name is not always available
                if fuel_icon := fuel_type.get("IconFileNameBase", ""):
                    for fuel, types in FUEL_TYPES_MAPPING.items():
                        if fuel_icon.replace(".png", "") in types:
                            apply_yes_no(fuel, item, True)
                            break
                    else:
                        self.logger.warning(f"Unknown fuel type: {fuel_type}")
                        self.crawler.stats.inc_value(f"atp/lukoil/fuel/failed/{fuel_icon}")
