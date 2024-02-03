import scrapy
from scrapy.http import JsonRequest

from locations.categories import Access, Categories, Extras, Fuel, PaymentMethods, apply_category, apply_yes_no
from locations.dict_parser import DictParser

BRANDS_MAPPING = {
    31: ("Газпромнефть", "Q1461799"),
    50000005: ("ОПТИ", "Q109356512"),
}

FUEL_MAPPING = {
    # Fuel descriptions are in 'oilProducts' key of JSON response.
    # Duplicate values in below mapping are due to
    # differently branded options for the same type of fuel.
    12: Fuel.OCTANE_95,
    421: Fuel.OCTANE_95,
    100034: Fuel.OCTANE_95,
    21: Fuel.OCTANE_98,
    422: Fuel.OCTANE_98,
    61: Fuel.OCTANE_80,
    62: Fuel.OCTANE_92,
    431: Fuel.OCTANE_92,
    100033: Fuel.OCTANE_92,
    372: Fuel.DIESEL,
    424: Fuel.DIESEL,
    461: Fuel.DIESEL,
    511: Fuel.DIESEL,
    512: Fuel.DIESEL,
    521: Fuel.DIESEL,
    541: Fuel.DIESEL,
    373: Fuel.LPG,
    531: Fuel.CNG,
    374: Fuel.COLD_WEATHER_DIESEL,
    423: Fuel.COLD_WEATHER_DIESEL,
    100001: Fuel.COLD_WEATHER_DIESEL,
    100032: Fuel.OCTANE_100,
    100036: Fuel.OCTANE_100,
}

SERVICES_MAPPING = {
    "adblue": Fuel.ADBLUE,
    "autowash": Extras.CAR_WASH,
    "cashmachine": Extras.ATM,
    "charge-electric": Fuel.ELECTRIC,
    "coffee": None,
    "dizel": Fuel.HGV_DIESEL,
    "fueler": "full_service",
    "handwash": Extras.CAR_WASH,
    "paycash": PaymentMethods.CASH,
    "pumping": Extras.COMPRESSED_AIR,
    "paycardmps": PaymentMethods.CARDS,
    "paycardgpn": "payment:gazpromneft",  # Not so common to add to FuelCards
    "paymobile": PaymentMethods.APP,
    "paycardnmp": "payment:gazpromneft",
    "paysbp": PaymentMethods.SBP,
    "postpay": None,
    "shop": None,
    "toilet": Extras.TOILETS,
    "track-parking": Access.HGV,
    "vacuum": Extras.VACUUM_CLEANER,
    "water": Extras.DRINKING_WATER,
}


class GazpromneftRUSpider(scrapy.Spider):
    name = "gazpromneft_ru"
    requires_proxy = "RU"

    def start_requests(self):
        yield JsonRequest("https://gpnbonus.ru/api/stations/list", method="POST")

    def parse(self, response):
        data = response.json()
        for poi in data["stations"]:
            item = DictParser.parse(poi)
            item["street_address"] = item.pop("addr_full", None)
            self.parse_hours(item, poi)
            self.parse_brand(item, poi)
            self.parse_fuel(item, poi)
            self.parse_services(item, poi)
            apply_category(Categories.FUEL_STATION, item)
            yield item

    def parse_hours(self, item, poi):
        if hours := poi.get("workMode"):
            if hours == "круглосуточно":
                item["opening_hours"] = "24/7"
            else:
                # TODO: other hours, only 20 POIs have them
                # self.logger.info(f'hours: {hours}')
                pass

    def parse_brand(self, item, poi):
        if tags := BRANDS_MAPPING.get(poi["brand_id"]):
            item["brand"], item["brand_wikidata"] = tags
        else:
            self.crawler.stats.inc_value(f"atp/gazpromneft_ru/unknown_brand/{poi['brand_id']}")

    def parse_fuel(self, item, poi):
        if oils := poi.get("oils"):
            for oil in oils:
                if tag := FUEL_MAPPING.get(oil):
                    apply_yes_no(tag, item, True)
                else:
                    self.crawler.stats.inc_value(f"atp/gazpromneft_ru/fuel/failed/{oil}")

    def parse_services(self, item, poi):
        if services := poi.get("services"):
            for service_category in services:
                for service in services[service_category]:
                    if tag := SERVICES_MAPPING.get(service):
                        apply_yes_no(tag, item, True)
                    else:
                        self.crawler.stats.inc_value(f"atp/gazpromneft_ru/service/failed/{service}")
