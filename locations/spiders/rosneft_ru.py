import scrapy
from scrapy.http import Response

from locations.categories import Categories, Extras, Fuel, PaymentMethods, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.items import Feature


class RosneftRUSpider(scrapy.Spider):
    name = "rosneft_ru"
    start_urls = ["https://rosneft-azs.ru/front-api/stations"]

    brands = {
        "rosneft": {"brand_wikidata": "Q1141123"},
        "tnk": {"brand_wikidata": "Q2298901"},
        "slavneft": {"brand_wikidata": "Q3486584"},
        "ptk": {"brand_wikidata": "Q4360193"},
    }
    fuel_types = {
        "ai98": Fuel.OCTANE_98,
        "ai95": Fuel.OCTANE_95,
        "ai95_fora": Fuel.AVJetA1,
        "ai92": Fuel.OCTANE_92,
        "ai92_fora": Fuel.OCTANE_92,
        "ai100": Fuel.OCTANE_100,
        "ai100_fora": Fuel.OCTANE_100,
        "diesel": Fuel.DIESEL,
        "diesel_fora": Fuel.DIESEL,
        "gaz": Fuel.LPG,
        "methane": Fuel.CNG,
    }
    services = {
        "shop": None,
        "cafe": Extras.FAST_FOOD,
        "qrpay": None,
        "chemistry": None,  # They mean pharmacy
        "wash": Extras.CAR_WASH,
        "tire": "service:vehicle:tyres",
        "hotel": None,
        "electro": "fuel:electricity",
        "cash": PaymentMethods.CASH,
        "finmarket": None,
    }

    def parse(self, response: Response):
        for poi in response.json()["data"]["stations"]:
            if poi.get("type") != "gas_station":
                self.crawler.stats.inc_value(f'atp/{self.name}/unknown_type/{poi.get("type")}')
                continue
            item = DictParser.parse(poi)
            item.pop("state")
            item["branch"] = poi.get("number")
            item["lat"] = poi["coordinate"]["lat"]
            item["lon"] = poi["coordinate"]["lng"]
            self.parse_brand(item, poi)
            self.parse_fuel(item, poi)
            self.parse_services(item, poi)
            apply_category(Categories.FUEL_STATION, item)
            yield item

    def parse_brand(self, item: Feature, poi: dict):
        brand = poi.get("brand")
        if brand:
            brand = brand.lower()
            if brand in self.brands:
                item.update(self.brands[brand])
            else:
                self.crawler.stats.inc_value(f"atp/{self.name}/unknown_brand/{brand}")

    def parse_fuel(self, item: Feature, poi: dict):
        for fuel in poi.get("fuels", []):
            if match := self.fuel_types.get(fuel["code"]):
                apply_yes_no(match, item, True)
            else:
                self.crawler.stats.inc_value(f'atp/{self.name}/fuel/failed/{fuel["code"]}')

    def parse_services(self, item: Feature, poi: dict):
        for service in poi.get("services", []):
            if match := self.services.get(service):
                apply_yes_no(match, item, True)
            else:
                self.crawler.stats.inc_value(f"atp/{self.name}/service/failed/{service}")
